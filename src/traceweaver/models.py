"""Validated graph entities and explicit JSON response shapes."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class Entity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    demo: Literal[True]
    dataset_id: str
    environment: str


class TimedEntity(Entity):
    timestamp: str

    @field_validator("timestamp")
    @classmethod
    def timezone_required(cls, value: str) -> str:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("Timestamps must include a timezone")
        return value


class Incident(TimedEntity):
    title: str
    summary: str
    severity: str
    status: str


class Service(Entity):
    name: str
    description: str


class Deployment(TimedEntity):
    name: str
    description: str
    source: str
    source_ref: str


class Change(TimedEntity):
    name: str
    description: str
    source: str
    source_ref: str


class Evidence(TimedEntity):
    summary: str
    description: str
    source: str
    source_ref: str


class Alert(TimedEntity):
    name: str
    severity: str
    source: str
    source_ref: str


class GraphStats(BaseModel):
    node_count: int
    relationship_count: int


class Health(GraphStats):
    status: Literal["ok"] = "ok"
    database_engine: Literal["relate"] = "relate"
    persistent_store: Literal[True] = True


class IncidentSummary(BaseModel):
    id: str
    title: str
    status: str
    severity: str


class DependencyPath(BaseModel):
    affected_service: Service
    dependency_service: Service
    service_ids: list[str]
    relationship_types: list[str]
    hop_count: int


class RelatedDeployment(BaseModel):
    service: Service
    deployment: Deployment
    change: Change


class EvidenceObservation(BaseModel):
    evidence: Evidence
    service: Service


class ContextPath(BaseModel):
    incident_id: str
    affected_service_id: str
    dependency_service_id: str
    deployment_id: str
    change_id: str
    relationship_types: list[str]


class IncidentContext(BaseModel):
    incident: Incident
    affected_services: list[Service]
    dependency_paths: list[DependencyPath]
    related_deployments: list[RelatedDeployment]
    evidence: list[EvidenceObservation]
    alerts: list[Alert]
    context_paths: list[ContextPath]
    interpretation: str = (
        "Graph connections are observed context, not proof that a deployment caused the incident."
    )
    dependency_depth_limit: int = 3
    result_limit: int = 100
    results_may_be_truncated: bool = False
