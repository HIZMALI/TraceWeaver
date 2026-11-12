"""Bounded, parameterized Cypher reads; all context comes from graph relationships."""

from traceweaver.models import IncidentContext
from traceweaver.storage import GraphStore

LIMIT = 100

INCIDENT_LOOKUP = """
MATCH (i:Incident {id: $incident_id})
RETURN properties(i) AS incident LIMIT 1
"""
INCIDENT_LIST = """
MATCH (i:Incident)
RETURN i.id AS id, i.title AS title, i.status AS status, i.severity AS severity
ORDER BY id LIMIT $limit
"""
AFFECTED_SERVICES = """
MATCH (:Incident {id: $incident_id})-[:AFFECTS]->(s:Service)
RETURN DISTINCT properties(s) AS service ORDER BY service.id LIMIT $limit
"""
DEPENDENCIES = """
MATCH (:Incident {id: $incident_id})-[:AFFECTS]->(s:Service)
MATCH p = (s)-[:DEPENDS_ON*1..3]->(d:Service)
RETURN DISTINCT properties(s) AS affected_service, properties(d) AS dependency_service,
       [n IN nodes(p) | n.id] AS service_ids,
       [r IN relationships(p) | type(r)] AS relationship_types, length(p) AS hop_count
ORDER BY affected_service.id, dependency_service.id, hop_count, service_ids LIMIT $limit
"""
RELATED_DEPLOYMENTS = """
MATCH (:Incident {id: $incident_id})-[:AFFECTS]->(s:Service)
MATCH (s)-[:DEPENDS_ON*0..3]->(target:Service)<-[:TARGETS]-(d:Deployment)
      -[:INCLUDES_CHANGE]->(c:Change)
RETURN DISTINCT properties(target) AS service, properties(d) AS deployment,
       properties(c) AS change
ORDER BY deployment.timestamp, deployment.id, change.id, service.id LIMIT $limit
"""
EVIDENCE = """
MATCH (:Incident {id: $incident_id})-[:HAS_EVIDENCE]->(e:Evidence)
      -[:OBSERVED_ON]->(s:Service)
RETURN properties(e) AS evidence, properties(s) AS service
ORDER BY e.timestamp, e.id, s.id LIMIT $limit
"""
ALERTS = """
MATCH (a:Alert)-[:RAISED_FOR]->(:Incident {id: $incident_id})
RETURN properties(a) AS alert ORDER BY a.timestamp, a.id LIMIT $limit
"""
MULTI_HOP_CONTEXT = """
MATCH (i:Incident {id: $incident_id})-[:AFFECTS]->(s:Service)
      -[:DEPENDS_ON]->(dependency:Service)<-[:TARGETS]-(d:Deployment)
      -[:INCLUDES_CHANGE]->(c:Change)
RETURN DISTINCT i.id AS incident_id, s.id AS affected_service_id,
       dependency.id AS dependency_service_id, d.id AS deployment_id, c.id AS change_id,
       ['AFFECTS', 'DEPENDS_ON', 'TARGETS', 'INCLUDES_CHANGE'] AS relationship_types
ORDER BY affected_service_id, dependency_service_id, deployment_id, change_id LIMIT $limit
"""


class IncidentNotFound(LookupError):
    """No incident with the given ID exists in this store."""


def list_incidents(store: GraphStore) -> list[dict]:
    return store.execute(INCIDENT_LIST, {"limit": LIMIT})


def incident_context(store: GraphStore, incident_id: str) -> IncidentContext:
    params = {"incident_id": incident_id, "limit": LIMIT}
    rows = store.execute(INCIDENT_LOOKUP, params)
    if not rows:
        raise IncidentNotFound(incident_id)
    affected = store.execute(AFFECTED_SERVICES, params)
    dependencies = store.execute(DEPENDENCIES, params)
    deployments = store.execute(RELATED_DEPLOYMENTS, params)
    evidence = store.execute(EVIDENCE, params)
    alerts = store.execute(ALERTS, params)
    paths = store.execute(MULTI_HOP_CONTEXT, params)
    return IncidentContext(
        incident=rows[0]["incident"],
        affected_services=[row["service"] for row in affected],
        dependency_paths=dependencies,
        related_deployments=deployments,
        evidence=evidence,
        alerts=[row["alert"] for row in alerts],
        context_paths=paths,
        results_may_be_truncated=any(
            len(result) == LIMIT
            for result in (affected, dependencies, deployments, evidence, alerts, paths)
        ),
    )
