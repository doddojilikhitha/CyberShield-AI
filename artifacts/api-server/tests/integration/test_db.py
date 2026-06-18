import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import (
    init_db,
    create_incident,
    get_incident,
    list_incidents,
    create_or_update_playbook,
    get_playbook,
    create_or_update_report,
    get_report_db,
    create_workflow_run,
    update_workflow_run,
    get_workflow_runs,
)

# Use in-memory SQLite database for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    # Setup test engine
    from db import database

    original_engine = database.engine
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    database.engine = engine

    # Init tables
    init_db()

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        database.engine = original_engine


def test_incident_operations(db_session):
    data = {
        "incident_description": "Suspicious exfiltration on port 443",
        "analyst_name": "test_user",
        "incident_source": "SIEM",
        "priority": "high",
    }

    incident = create_incident(db_session, data)
    assert incident["incident_id"] is not None
    assert incident["incident_description"] == data["incident_description"]

    retrieved = get_incident(db_session, incident["incident_id"])
    assert retrieved is not None
    assert retrieved["analyst_name"] == "test_user"

    all_incidents = list_incidents(db_session)
    assert len(all_incidents) == 1


def test_playbook_operations(db_session):
    incident_id = "test-incident-uuid"
    playbook_data = {
        "incident_type": "phishing",
        "severity": "medium",
        "generated_playbook": "# Response Playbook",
        "review_status": "pending_review",
    }

    create_or_update_playbook(db_session, incident_id, playbook_data)

    playbook = get_playbook(db_session, incident_id)
    assert playbook is not None
    assert playbook["incident_type"] == "phishing"
    assert playbook["review_status"] == "pending_review"


def test_report_and_workflow_runs(db_session):
    incident_id = "test-report-uuid"
    report_data = {"incident_id": incident_id, "summary": "Sample report summary data"}

    create_or_update_report(
        db_session, incident_id, report_data, pdf_path="/tmp/path.pdf"
    )
    report = get_report_db(db_session, incident_id)
    assert report is not None
    assert report["report_data"]["summary"] == "Sample report summary data"

    run_id = "workflow-run-1"
    create_workflow_run(db_session, run_id, incident_id, "started")
    update_workflow_run(
        db_session, run_id, {"status": "completed", "duration_ms": 1500}
    )

    runs = get_workflow_runs(db_session, incident_id)
    assert len(runs) == 1
    assert runs[0]["status"] == "completed"
    assert runs[0]["duration_ms"] == 1500
