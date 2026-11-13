"""Dedicated read-only public surface for the exact immutable synthetic judge bundle."""

import hashlib
import logging
import os
import re
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from traceweaver.agent_models import AgentInvestigationReport, AgentScopeRequest
from traceweaver.agent_rehearsal import run_rehearsal
from traceweaver.dashboard import console_incidents, dashboard
from traceweaver.dashboard_models import ConsoleIncidents, DashboardBundle
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.judge_demo import ARTIFACT_NAME, MANIFEST_NAME, verify_judge_demo
from traceweaver.local_files import read_local_bytes
from traceweaver.queries import IncidentNotFound
from traceweaver.storage import StorageError
from traceweaver.tool_errors import ToolError

logger = logging.getLogger(__name__)
DATABASE_SHA256 = "29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239"
MANIFEST_SHA256 = "50bdfbf4f700aedd13b099cc8cb5224141ccdd3c917fd32f2373be6187741aab"
DASHBOARD_PATH = re.compile(r"/incidents/([A-Za-z0-9][A-Za-z0-9_.:-]{0,63})/dashboard")
REHEARSAL_PATH = re.compile(r"/public/rehearsal/([A-Za-z0-9][A-Za-z0-9_.:-]{0,63})")
AUTHORITY = re.compile(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?(?::[1-9][0-9]{0,4})?")
ASSET_NAME = re.compile(r"index-[A-Za-z0-9_-]+\.(?:js|css)")
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; "
    "base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
)


@dataclass(frozen=True)
class PublicSettings:
    bundle: Path
    hosts: tuple[str, ...]
    assets: Path | None = None
    allow_http: bool = False

    @classmethod
    def from_environment(cls):
        hosts = os.environ.get("TRACEWEAVER_PUBLIC_HOSTS") or os.environ.get(
            "RENDER_EXTERNAL_HOSTNAME", ""
        )
        return cls(
            bundle=Path(os.environ.get("TRACEWEAVER_PUBLIC_BUNDLE", "examples/judge-demo")),
            hosts=tuple(host.strip() for host in hosts.split(",") if host.strip()),
            allow_http=os.environ.get("TRACEWEAVER_PUBLIC_ALLOW_HTTP") == "1",
        )

    def validate(self):
        if not 1 <= len(self.hosts) <= 5 or len(set(self.hosts)) != len(self.hosts):
            raise ValueError("Explicit unique public hosts required")
        for host in self.hosts:
            if not AUTHORITY.fullmatch(host) or ".." in host or host.startswith("-"):
                raise ValueError("Invalid public host")
            if ":" in host and int(host.rsplit(":", 1)[1]) > 65535:
                raise ValueError("Invalid public port")
            if self.allow_http and host.split(":", 1)[0] != "127.0.0.1":
                raise ValueError("HTTP is restricted to explicit numeric loopback test hosts")


class ReadAdmission:
    """Constant-space process-wide budget; never trust client-supplied forwarding identities."""

    def __init__(self):
        self.lock = threading.Lock()
        self.active = 0
        self.tokens = 60.0
        self.updated = time.monotonic()

    def enter(self, cost=1):
        with self.lock:
            now = time.monotonic()
            self.tokens = min(60.0, self.tokens + max(0.0, now - self.updated) * 2.0)
            self.updated = now
            if self.active >= 2 or self.tokens < cost:
                return False
            self.tokens -= cost
            self.active += 1
            return True

    def leave(self):
        with self.lock:
            self.active -= 1


class PublicResources:
    def __init__(self, settings):
        self.settings = settings
        self.database = settings.bundle / ARTIFACT_NAME
        self.directory = settings.assets or Path(
            str(files("traceweaver").joinpath("public_static"))
        )
        self.assets = frozenset()
        self.ready = False
        self.admission = ReadAdmission()

    def require_intact(self):
        for path, expected in (
            (self.database, DATABASE_SHA256),
            (self.settings.bundle / MANIFEST_NAME, MANIFEST_SHA256),
        ):
            limit = 110592 if path == self.database else 8192
            if (
                path.is_symlink()
                or path.stat().st_size > limit
                or hashlib.sha256(read_local_bytes(path)).hexdigest() != expected
            ):
                raise ValueError("Public artifact unavailable")

    def verify(self):
        self.settings.validate()
        self.require_intact()
        manifest = verify_judge_demo(self.settings.bundle)
        if manifest["graph_counts"] != {"node_count": 51, "relationship_count": 67}:
            raise ValueError("Unexpected public graph")
        index = self.directory / "index.html"
        if self.directory.is_symlink() or index.is_symlink() or index.stat().st_size > 32768:
            raise ValueError("Public console unavailable")
        html = index.read_text(encoding="utf8")
        if not re.search(r'<meta\s+name="traceweaver-mode"\s+content="public"', html):
            raise ValueError("Dedicated public console build required")
        assets = re.findall(r'(?:src|href)="/assets/([^"/]+)"', html)
        if (
            len(assets) != 2
            or sum(name.endswith(".js") for name in assets) != 1
            or sum(name.endswith(".css") for name in assets) != 1
            or not all(ASSET_NAME.fullmatch(name) for name in assets)
        ):
            raise ValueError("Unexpected public assets")
        assets.append("third-party-licenses.txt")
        for name in assets:
            path = self.directory / "assets" / name
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
                raise ValueError("Public asset unavailable")
        self.assets = frozenset(assets)
        self.require_intact()
        self.ready = True

    def read(self, function, *args):
        try:
            self.require_intact()
            result = function(self.database, *args)
            self.require_intact()
            return result
        except IncidentNotFound:
            raise HTTPException(404, "Incident not found") from None
        except ToolError as exc:
            if exc.code == "STALE_SNAPSHOT":
                raise HTTPException(409, "Public snapshot changed; refresh") from None
            raise HTTPException(503, "Public graph unavailable") from None
        except (StorageError, OSError, ValueError, ValidationError):
            raise HTTPException(503, "Public graph unavailable") from None


class PublicBoundary:
    """Fail closed independently of the unchanged loopback-only local application."""

    def __init__(self, app, resources):
        self.app, self.resources = app, resources

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            return await send({"type": "websocket.close", "code": 1008})
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        state, path, headers = self.resources, scope["path"], scope.get("headers", [])
        started = False

        async def safe_send(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                extra = {
                    b"content-security-policy": CSP.encode(),
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"referrer-policy": b"no-referrer",
                    b"permissions-policy": b"camera=(), microphone=(), geolocation=(), payment=()",
                    b"cache-control": b"no-store",
                }
                if not state.settings.allow_http:
                    extra[b"strict-transport-security"] = b"max-age=31536000"
                present = dict(message.get("headers", []))
                message["headers"] = list({**extra, **present}.items())
            await send(message)

        async def reject(status, detail, **extra):
            await JSONResponse({"detail": detail}, status_code=status, headers=extra)(
                scope, receive, safe_send
            )

        hosts = [v.decode("latin1") for k, v in headers if k == b"host"]
        origins = [v.decode("latin1") for k, v in headers if k == b"origin"]
        if len(hosts) != 1 or hosts[0] not in state.settings.hosts:
            return await reject(403, "Public host not allowed")
        scheme = "http" if state.settings.allow_http else "https"
        if origins and origins != [scheme + "://" + hosts[0]]:
            return await reject(403, "Public origin not allowed")
        asset = path.removeprefix("/assets/") if path.startswith("/assets/") else None
        rehearsal = bool(REHEARSAL_PATH.fullmatch(path))
        graph = path == "/console/incidents" or bool(DASHBOARD_PATH.fullmatch(path)) or rehearsal
        if (
            len(path) > 256
            or scope.get("raw_path", path.encode()) != path.encode()
            or not (path in {"/", "/health"} or graph or asset in state.assets)
        ):
            return await reject(404, "Not found")
        if scope["method"] != "GET":
            return await reject(405, "Method not allowed", Allow="GET")
        if (
            len(scope.get("query_string", b"")) > 2048
            or sum(len(k) + len(v) for k, v in headers) > 16384
        ):
            return await reject(400, "Request exceeds public limits")
        if any(
            k == b"transfer-encoding" or (k == b"content-length" and v != b"0") for k, v in headers
        ):
            return await reject(400, "Request body not allowed")
        if not state.ready:
            return await reject(503, "Public demo unavailable")
        if graph and not state.admission.enter(cost=4 if rehearsal else 1):
            return await reject(429, "Public demo busy", **{"Retry-After": "2"})
        try:
            await self.app(scope, receive, safe_send)
        except Exception as exc:
            logger.error("Public request failed: %s", type(exc).__name__)
            if started:
                raise RuntimeError("Public response interrupted") from None
            await reject(500, "Public request failed")
        finally:
            if graph:
                state.admission.leave()


def public_options(request, extra_fields=frozenset()):
    values = request.query_params.multi_items()
    allowed = set(InvestigationOptions.model_fields)
    if len(values) > 4 + len(extra_fields) or len({key for key, _ in values}) != len(values):
        raise HTTPException(422, "Invalid public options")
    values = [(key, value) for key, value in values if key not in extra_fields]
    if any(key not in allowed or not re.fullmatch(r"[0-9]{1,4}", value) for key, value in values):
        raise HTTPException(422, "Invalid public options")
    try:
        return InvestigationOptions(**{key: int(value) for key, value in values})
    except ValidationError:
        raise HTTPException(422, "Invalid public options") from None


def create_app(settings: PublicSettings | None = None):
    resources = PublicResources(settings or PublicSettings.from_environment())

    @asynccontextmanager
    async def lifespan(application):
        try:
            await run_in_threadpool(resources.verify)
        except Exception:
            raise RuntimeError("Public demo startup validation failed") from None
        try:
            yield
        finally:
            resources.ready = False

    application = FastAPI(
        title="TraceWeaver public synthetic demo",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        redirect_slashes=False,
    )
    application.state.public_resources = resources
    application.add_middleware(PublicBoundary, resources=resources)

    @application.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        return JSONResponse({"detail": "Invalid public request"}, status_code=422)

    @application.get("/health")
    def health():
        try:
            resources.require_intact()
        except (OSError, ValueError):
            raise HTTPException(503, "Public graph unavailable") from None
        return {"status": "ok", "database_engine": "relate", "synthetic": True, "read_only": True}

    @application.get("/console/incidents", response_model=ConsoleIncidents)
    def incidents(request: Request):
        if request.query_params:
            raise HTTPException(422, "Invalid public options")
        return resources.read(console_incidents)

    @application.get("/incidents/{incident_id}/dashboard", response_model=DashboardBundle)
    def incident(request: Request, incident_id: str):
        return resources.read(dashboard, incident_id, public_options(request))

    @application.get("/", include_in_schema=False)
    def index():
        return FileResponse(resources.directory / "index.html", media_type="text/html")

    @application.get("/public/rehearsal/{incident_id}", response_model=AgentInvestigationReport)
    def rehearsal(request: Request, incident_id: str):
        options = public_options(request, frozenset({"source_fingerprint", "intent"}))
        fingerprint = request.query_params.get("source_fingerprint", "")
        if not re.fullmatch(r"[a-f0-9]{64}", fingerprint):
            raise HTTPException(422, "Invalid public options")
        try:
            # A server-defined read-only plan is never confirmation for model inference.
            action = AgentScopeRequest(
                incident_id=incident_id,
                options=options,
                source_fingerprint=fingerprint,
                intent=request.query_params.get("intent", "TRACE_DEPENDENCY_PATH"),
                confirmed=True,
            )
        except ValidationError:
            raise HTTPException(422, "Invalid public options") from None
        report = resources.read(run_rehearsal, action)
        if (
            report.mode_executed != "DETERMINISTIC_TOOL_REHEARSAL"
            or report.ai_directed_tools
            or report.ai_generated_selection
            or report.model_interactions
            or report.model_requested
            or report.model_executed
        ):
            raise HTTPException(503, "Public rehearsal unavailable")
        return report

    @application.get("/assets/{name}", include_in_schema=False)
    def asset(name: str):
        if name not in resources.assets:
            raise HTTPException(404, "Not found")
        return FileResponse(
            resources.directory / "assets" / name,
            headers={"Cache-Control": "public, max-age=3600"},
        )

    return application


app = create_app()
