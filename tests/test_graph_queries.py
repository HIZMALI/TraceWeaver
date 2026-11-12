import pytest

from traceweaver.queries import (
    AFFECTED_SERVICES,
    DEPENDENCIES,
    EVIDENCE,
    INCIDENT_LOOKUP,
    MULTI_HOP_CONTEXT,
    RELATED_DEPLOYMENTS,
    IncidentNotFound,
    incident_context,
)
from traceweaver.storage import GraphStore


def test_multi_hop_traversal(database):
    with GraphStore(database) as store:
        result = store.execute(MULTI_HOP_CONTEXT, {"incident_id": "INC-001", "limit": 100})
    assert result == [
        {
            "incident_id": "INC-001",
            "affected_service_id": "SVC-PAYMENT",
            "dependency_service_id": "SVC-AUTH",
            "deployment_id": "DEP-001",
            "change_id": "CHG-001",
            "relationship_types": ["AFFECTS", "DEPENDS_ON", "TARGETS", "INCLUDES_CHANGE"],
        }
    ]


def test_incident_isolation(database):
    with GraphStore(database) as store:
        context = incident_context(store, "INC-002")
    assert context.incident.id == "INC-002"
    assert {service.id for service in context.affected_services} == {"SVC-NOTIFICATION"}
    assert {path.dependency_service.id for path in context.dependency_paths} == {"SVC-QUEUE"}
    assert {row.deployment.id for row in context.related_deployments} == {"DEP-003"}
    assert {row.evidence.id for row in context.evidence} == {"EVD-005", "EVD-006"}
    assert {row.change_id for row in context.context_paths} == {"CHG-003"}
    assert {alert.id for alert in context.alerts} == {"ALT-002"}


def test_candidate_deployments_and_evidence_provenance(database):
    with GraphStore(database) as store:
        context = incident_context(store, "INC-001")
    assert {row.deployment.id for row in context.related_deployments} == {"DEP-001", "DEP-002"}
    assert len(context.evidence) == 4
    assert len({row.evidence.source for row in context.evidence}) == 4
    assert all(row.evidence.timestamp.endswith("Z") for row in context.evidence)
    assert all(row.evidence.source_ref.startswith("demo://") for row in context.evidence)
    assert any(path.hop_count == 2 for path in context.dependency_paths)


def test_traversal_depends_on_relationships_not_names(database):
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "MATCH (s:Service {id: $id}) SET s.name = $name",
            {"id": "SVC-AUTH", "name": "Unrelated display name"},
        )
        context = incident_context(store, "INC-001")
    assert context.context_paths[0].deployment_id == "DEP-001"
    assert any(
        p.dependency_service.name == "Unrelated display name" for p in context.dependency_paths
    )


@pytest.mark.parametrize("value", ["unknown", "INC-001' OR true //", "' MATCH (n) RETURN n //"])
def test_parameter_safety(database, value):
    with GraphStore(database) as store:
        with pytest.raises(IncidentNotFound):
            incident_context(store, value)
        assert store.counts() == {"node_count": 21, "relationship_count": 27}
    for query in (
        INCIDENT_LOOKUP,
        AFFECTED_SERVICES,
        DEPENDENCIES,
        RELATED_DEPLOYMENTS,
        EVIDENCE,
        MULTI_HOP_CONTEXT,
    ):
        assert "$incident_id" in query
        assert value not in query
