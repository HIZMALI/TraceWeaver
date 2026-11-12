import pytest

from traceweaver.explanation_catalog import build_catalog
from traceweaver.investigation import investigate
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.storage import GraphStore


@pytest.fixture
def read_investigation():
    def read(database, incident="INC-001", **options):
        with GraphStore(database) as store:
            return investigate(store, incident, InvestigationOptions(**options))

    return read


@pytest.fixture
def baseline_context(database, read_investigation):
    return read_investigation(database)


@pytest.fixture
def scenario_context(case_database, read_investigation):
    return read_investigation(case_database, "CASE-INC")


@pytest.fixture
def scenario_catalog(scenario_context):
    return build_catalog(scenario_context)
