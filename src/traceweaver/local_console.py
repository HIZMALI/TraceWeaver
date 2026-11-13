"""Strict numeric-loopback boundary for the new console, without changing legacy APIs."""

from starlette.responses import JSONResponse


def console_path(path):
    return path == "/" or path.startswith(("/assets/", "/console/")) or path.endswith("/dashboard")


def local_origin(scope):
    server = scope.get("server")
    if not server or server[0] != "127.0.0.1" or scope.get("scheme") != "http":
        return None
    return "http://127.0.0.1" + (f":{server[1]}" if server[1] != 80 else "")


class LocalConsoleBoundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not console_path(scope["path"]):
            return await self.app(scope, receive, send)
        origin = local_origin(scope)
        headers = scope.get("headers", [])
        hosts = [v.decode("latin-1") for k, v in headers if k == b"host"]
        origins = [v.decode("latin-1") for k, v in headers if k == b"origin"]
        expected_host = origin.removeprefix("http://") if origin else None
        allowed_hosts = {expected_host}
        if scope.get("server", (None, None))[1] == 80:
            allowed_hosts.add("127.0.0.1:80")
        if (
            not origin
            or len(hosts) != 1
            or hosts[0] not in allowed_hosts
            or (origins and origins != [origin])
        ):
            return await JSONResponse({"detail": "Local console origin required"}, status_code=403)(
                scope, receive, send
            )
        if scope["method"] == "POST" and (
            origins != [origin] or scope.get("client", (None,))[0] != "127.0.0.1"
        ):
            return await JSONResponse(
                {"detail": "Same-origin local action required"}, status_code=403
            )(scope, receive, send)

        async def safe_send(message):
            if message["type"] == "http.response.start":
                extra = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                ]
                if scope["path"].startswith("/console/") or scope["path"].endswith("/dashboard"):
                    extra.append((b"cache-control", b"no-store"))
                existing = {k for k, _ in message.get("headers", [])}
                message["headers"] = message.get("headers", []) + [
                    p for p in extra if p[0] not in existing
                ]
            await send(message)

        await self.app(scope, receive, safe_send)
