"""Minimal read-only HTTP surface over the actual Relate store."""

import logging
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BeforeValidator, ValidationError

from traceweaver.config import Settings
from traceweaver.dashboard import console_incidents, dashboard
from traceweaver.dashboard_models import ConsoleIncidents, DashboardBundle
from traceweaver.explanation import explain
from traceweaver.explanation_models import ExplanationReport
from traceweaver.investigation import investigate
from traceweaver.investigation_models import Investigation, InvestigationOptions
from traceweaver.models import Health, IncidentContext, IncidentSummary
from traceweaver.queries import IncidentNotFound, incident_context, list_incidents
from traceweaver.storage import GraphStore, StorageError
from traceweaver.temporal import integer_query
from traceweaver.tool_errors import ToolError
from traceweaver.web_assets import mount_console

logger = logging.getLogger(__name__)
WindowMinutes = Annotated[int, BeforeValidator(integer_query), Query(ge=0, le=1440)]
ResultLimit = Annotated[int, BeforeValidator(integer_query), Query(ge=1, le=100)]


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    application = FastAPI(
        title="TraceWeaver", version="0.1.0", description="Read-only graph incident context"
    )

    @application.exception_handler(StorageError)
    async def unavailable_handler(request, exc):
        return JSONResponse(status_code=503, content={"detail": "Graph database unavailable"})

    @application.exception_handler(ValidationError)
    async def invalid_graph_handler(request, exc):
        return JSONResponse(status_code=503, content={"detail": "Graph data is incompatible"})

    @application.exception_handler(Exception)
    async def unexpected_handler(request, exc):
        logger.error("Unexpected TraceWeaver request failure", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    # A synchronous handler runs its entire with block in one worker thread. A yielded
    # dependency could open and close on different threads, which Relate forbids.
    @application.get("/health", response_model=Health)
    def health() -> Health:
        with GraphStore(config.database) as store:
            return Health(**store.counts())

    @application.get("/incidents", response_model=list[IncidentSummary])
    def incidents() -> list[IncidentSummary]:
        with GraphStore(config.database) as store:
            return [IncidentSummary.model_validate(row) for row in list_incidents(store)]

    @application.get("/incidents/{incident_id}/context", response_model=IncidentContext)
    def context(incident_id: str) -> IncidentContext:
        try:
            with GraphStore(config.database) as store:
                return incident_context(store, incident_id)
        except IncidentNotFound:
            raise HTTPException(status_code=404, detail="Incident not found") from None

    @application.get("/incidents/{incident_id}/investigation", response_model=Investigation)
    def investigation(
        incident_id: str,
        pre_minutes: WindowMinutes = 120,
        post_minutes: WindowMinutes = 30,
        max_candidates: ResultLimit = 100,
        max_evidence: ResultLimit = 100,
    ) -> Investigation:
        try:
            options = InvestigationOptions(
                pre_minutes=pre_minutes,
                post_minutes=post_minutes,
                max_candidates=max_candidates,
                max_evidence=max_evidence,
            )
            with GraphStore(config.database) as store:
                return investigate(store, incident_id, options)
        except IncidentNotFound:
            raise HTTPException(status_code=404, detail="Incident not found") from None

    @application.get("/incidents/{incident_id}/explanation", response_model=ExplanationReport)
    def explanation(
        incident_id: str,
        pre_minutes: WindowMinutes = 120,
        post_minutes: WindowMinutes = 30,
        max_candidates: ResultLimit = 100,
        max_evidence: ResultLimit = 100,
    ) -> ExplanationReport:
        try:
            options = InvestigationOptions(
                pre_minutes=pre_minutes,
                post_minutes=post_minutes,
                max_candidates=max_candidates,
                max_evidence=max_evidence,
            )
            # Shared service owns open/query/close in this same synchronous worker.
            # HTTP deliberately exposes no provider/model option.
            return explain(config.database, incident_id, options)
        except IncidentNotFound:
            raise HTTPException(status_code=404, detail="Incident not found") from None
        except ToolError:
            raise HTTPException(
                status_code=503, detail="Explanation context is incompatible"
            ) from None

    @application.get("/incidents/{incident_id}/dashboard", response_model=DashboardBundle)
    def dashboard_bundle(
        incident_id: str,
        pre_minutes: WindowMinutes = 120,
        post_minutes: WindowMinutes = 30,
        max_candidates: ResultLimit = 100,
        max_evidence: ResultLimit = 100,
    ) -> DashboardBundle:
        try:
            return dashboard(
                config.database,
                incident_id,
                InvestigationOptions(
                    pre_minutes=pre_minutes,
                    post_minutes=post_minutes,
                    max_candidates=max_candidates,
                    max_evidence=max_evidence,
                ),
            )
        except IncidentNotFound:
            raise HTTPException(status_code=404, detail="Incident not found") from None
        except ToolError:
            raise HTTPException(
                status_code=503, detail="Dashboard context is incompatible"
            ) from None

    @application.get("/console/incidents", response_model=ConsoleIncidents)
    def console_incident_list() -> ConsoleIncidents:
        return console_incidents(config.database)

    mount_console(application)
    return application


app = create_app()
