"""Explicit, allowlisted labels and directed relationship types."""

from traceweaver.models import Alert, Change, Deployment, Evidence, Incident, Service
from traceweaver.storage import GraphStore

ENTITY_MODELS = {
    "Incident": Incident,
    "Service": Service,
    "Deployment": Deployment,
    "Change": Change,
    "Evidence": Evidence,
    "Alert": Alert,
}

RELATIONSHIPS = {
    "AFFECTS": ("Incident", "Service"),
    "DEPENDS_ON": ("Service", "Service"),
    "TARGETS": ("Deployment", "Service"),
    "INCLUDES_CHANGE": ("Deployment", "Change"),
    "HAS_EVIDENCE": ("Incident", "Evidence"),
    "OBSERVED_ON": ("Evidence", "Service"),
    "RAISED_FOR": ("Alert", "Incident"),
}


def ensure_schema(store: GraphStore) -> None:
    for label in ENTITY_MODELS:
        # Identifiers come from this fixed mapping, never from an ID or free-form input.
        store.execute(
            f"CREATE CONSTRAINT traceweaver_{label.lower()}_id IF NOT EXISTS "
            f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
        )
