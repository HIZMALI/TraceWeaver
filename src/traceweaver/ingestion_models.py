"""Ingestion 1.0 is an independent contract, not demo-fixture schema_version 1/2."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, model_validator

from traceweaver.schema import ENTITY_MODELS, RELATIONSHIPS
from traceweaver.temporal import parse_timestamp

MAX_NODES = 2000
MAX_RELATIONSHIPS = 4000
MAX_STRING_BYTES = 4096
Label = Literal["Incident", "Service", "Deployment", "Change", "Evidence", "Alert"]
Scalar = StrictStr | StrictBool | None
PROPERTY_NAMES = {label: set(model.model_fields) for label, model in ENTITY_MODELS.items()}
PROPERTY_NAMES["Incident"] |= {"incident_started_at", "ingested_at"}
PROPERTY_NAMES["Deployment"] |= {"deployment_occurred_at", "ingested_at"}
PROPERTY_NAMES["Change"] |= {"ingested_at"}
PROPERTY_NAMES["Alert"] |= {"ingested_at"}
PROPERTY_NAMES["Service"] |= {"ingested_at"}
PROPERTY_NAMES["Evidence"] |= {
    "observed_at",
    "ingested_at",
    "signal_key",
    "observed_state",
    "service_id",
    "observation_window_start",
    "observation_window_end",
}
TIME_FIELDS = {
    "timestamp",
    "incident_started_at",
    "deployment_occurred_at",
    "observed_at",
    "ingested_at",
    "observation_window_start",
    "observation_window_end",
}


def check_text(value: str, *, identity: bool = False) -> None:
    limit = 128 if identity else MAX_STRING_BYTES
    if len(value.encode("utf-8")) > limit:
        raise ValueError("String exceeds its admitted UTF-8 byte limit")
    if identity and (
        not value.strip() or value != value.strip() or any(ord(c) < 32 for c in value)
    ):
        raise ValueError("Identity must be nonempty, trimmed, and free of control characters")


class ContractModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class IngestionSource(ContractModel):
    source_id: str
    kind: Literal["LOCAL_EXPORT"]
    declared_origin: Literal["SYNTHETIC", "NON_SYNTHETIC", "UNKNOWN"]
    captured_at: str
    description: str

    @model_validator(mode="after")
    def validate_source(self):
        check_text(self.source_id, identity=True)
        check_text(self.description)
        if not self.description.strip() or parse_timestamp(self.captured_at).utc is None:
            raise ValueError("Source requires a description and valid explicit-offset capture time")
        return self


class Endpoint(ContractModel):
    label: Label
    id: str

    @model_validator(mode="after")
    def validate_id(self):
        check_text(self.id, identity=True)
        return self


class IngestionNode(Endpoint):
    properties: dict[str, Scalar]

    @model_validator(mode="after")
    def validate_properties(self):
        if set(self.properties) - PROPERTY_NAMES[self.label]:
            raise ValueError("Unsupported property name")
        nullable = TIME_FIELDS | {"demo", "signal_key", "observed_state", "service_id"}
        if self.label == "Evidence":
            nullable |= {"source", "source_ref"}
        required = set(ENTITY_MODELS[self.label].model_fields) - nullable
        if not required <= self.properties.keys():
            raise ValueError("Required identity or display properties are missing")
        if self.properties["id"] != self.id:
            raise ValueError("Node and property IDs must agree")
        for name, value in self.properties.items():
            if name == "demo":
                if value is not None and type(value) is not bool:
                    raise ValueError("Demo marker must be a boolean or null")
            elif value is not None and not isinstance(value, str):
                raise ValueError(
                    "Properties other than demo must be strings or admitted null metadata"
                )
            elif value is None and name not in nullable:
                raise ValueError("Required properties cannot be null")
            if isinstance(value, str):
                check_text(value, identity=name in {"id", "dataset_id"})
                if name in required and not value.strip():
                    raise ValueError("Required display or identity properties cannot be empty")
        if "observed_state" in self.properties and self.properties["observed_state"] not in {
            None,
            "HEALTHY",
            "DEGRADED",
            "FAILED",
        }:
            raise ValueError("Unsupported structured observation state")
        return self


class IngestionRelationship(ContractModel):
    type: Literal[
        "AFFECTS",
        "DEPENDS_ON",
        "TARGETS",
        "INCLUDES_CHANGE",
        "HAS_EVIDENCE",
        "OBSERVED_ON",
        "RAISED_FOR",
    ]
    source: Endpoint
    target: Endpoint

    @model_validator(mode="after")
    def validate_direction(self):
        if (self.source.label, self.target.label) != RELATIONSHIPS[self.type]:
            raise ValueError("Relationship endpoint labels or direction are invalid")
        return self


class IngestionDocument(ContractModel):
    contract_version: Literal["1.0"]
    dataset_id: str
    source: IngestionSource
    nodes: Annotated[list[IngestionNode], Field(min_length=1, max_length=MAX_NODES)]
    relationships: Annotated[list[IngestionRelationship], Field(max_length=MAX_RELATIONSHIPS)]

    @model_validator(mode="after")
    def validate_graph(self):
        check_text(self.dataset_id, identity=True)
        identities = {(node.label, node.id): node for node in self.nodes}
        if len(identities) != len(self.nodes):
            raise ValueError("Duplicate node identity")
        keys = set()
        observed_links = set()
        for edge in self.relationships:
            source, target = (
                (edge.source.label, edge.source.id),
                (edge.target.label, edge.target.id),
            )
            if source not in identities or target not in identities:
                raise ValueError("Dangling relationship endpoint")
            key = (edge.type, source, target)
            if key in keys:
                raise ValueError("Duplicate relationship")
            keys.add(key)
            if edge.type == "OBSERVED_ON":
                observed_links.add((edge.source.id, edge.target.id))
        for node in self.nodes:
            if node.properties["dataset_id"] != self.dataset_id:
                raise ValueError("Dataset ownership is inconsistent")
            demo = node.properties.get("demo")
            if (self.source.declared_origin == "SYNTHETIC" and demo is not True) or (
                self.source.declared_origin == "NON_SYNTHETIC" and demo is not False
            ):
                raise ValueError("Declared origin conflicts with record demo metadata")
            service_id = node.properties.get("service_id")
            if service_id is not None and (node.id, service_id) not in observed_links:
                raise ValueError(
                    "Structured service_id lacks an actual OBSERVED_ON link in the batch"
                )
        return self
