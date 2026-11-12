"""Validated, atomic demo import without clearing or overwriting existing data."""

import json
from importlib.resources import files
from pathlib import Path

from pydantic import BaseModel, ConfigDict, JsonValue, model_validator

from traceweaver.schema import ENTITY_MODELS, RELATIONSHIPS, ensure_schema
from traceweaver.storage import GraphStore, QueryError


class FixtureNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str
    properties: dict[str, JsonValue]

    @model_validator(mode="after")
    def validate_entity(self) -> "FixtureNode":
        if self.label not in ENTITY_MODELS:
            raise ValueError("Unsupported node label")
        self.properties = ENTITY_MODELS[self.label].model_validate(self.properties).model_dump()
        return self


class FixtureRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str
    source: str
    target: str


class GraphFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_id: str
    description: str
    nodes: list[FixtureNode]
    relationships: list[FixtureRelationship]

    @model_validator(mode="after")
    def validate_graph(self) -> "GraphFixture":
        nodes = {node.properties["id"]: node for node in self.nodes}
        if len(nodes) != len(self.nodes):
            raise ValueError("Fixture IDs must be unique")
        edges = set()
        for node in self.nodes:
            if node.properties["dataset_id"] != self.dataset_id:
                raise ValueError("Every node must belong to the declared demo dataset")
        for edge in self.relationships:
            if edge.type not in RELATIONSHIPS:
                raise ValueError("Unsupported relationship type")
            if edge.source not in nodes or edge.target not in nodes:
                raise ValueError("Relationship endpoint does not exist")
            labels = (nodes[edge.source].label, nodes[edge.target].label)
            if labels != RELATIONSHIPS[edge.type]:
                raise ValueError("Relationship direction or endpoint labels are invalid")
            key = (edge.type, edge.source, edge.target)
            if key in edges:
                raise ValueError("Duplicate fixture relationship")
            edges.add(key)
        return self


def load_fixture(path: Path | None = None) -> GraphFixture:
    resource = path if path else files("traceweaver").joinpath("fixtures/demo_incidents.json")
    return GraphFixture.model_validate(json.loads(resource.read_text(encoding="utf-8")))


def seed_database(database: str | Path, fixture_path: Path | None = None) -> dict[str, int]:
    fixture = load_fixture(fixture_path)
    nodes = {node.properties["id"]: node for node in fixture.nodes}
    with GraphStore(database, read_only=False) as store:
        with store.transaction():
            ensure_schema(store)
            for node in fixture.nodes:
                label = node.label  # Validated against ENTITY_MODELS before any write.
                rows = store.execute(
                    f"MERGE (n:{label} {{id: $id}}) ON CREATE SET n += $properties "
                    "RETURN properties(n) AS properties LIMIT 1",
                    {"id": node.properties["id"], "properties": node.properties},
                )
                existing = rows[0]["properties"]
                if any(existing.get(key) != value for key, value in node.properties.items()):
                    raise QueryError(
                        f"Seed conflict for {label} {node.properties['id']}: "
                        "existing properties differ; no records were overwritten"
                    )
            for edge in fixture.relationships:
                source_label = nodes[edge.source].label
                target_label = nodes[edge.target].label
                store.execute(
                    f"MATCH (a:{source_label} {{id: $source}}), "
                    f"(b:{target_label} {{id: $target}}) "
                    f"MERGE (a)-[r:{edge.type}]->(b) "
                    "ON CREATE SET r.demo = true, r.dataset_id = $dataset_id",
                    {
                        "source": edge.source,
                        "target": edge.target,
                        "dataset_id": fixture.dataset_id,
                    },
                )
            counts = store.counts()
    return counts
