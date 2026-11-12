"""Minimal read-only HTTP surface over the actual Relate store."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from traceweaver.config import Settings
from traceweaver.models import Health, IncidentContext, IncidentSummary
from traceweaver.queries import IncidentNotFound, incident_context, list_incidents
from traceweaver.storage import GraphStore, StorageError


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

    return application


app = create_app()
