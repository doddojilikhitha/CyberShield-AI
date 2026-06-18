import pytest
from fastapi.testclient import TestClient
from main import app
from db.database import init_db


@pytest.fixture(scope="module")
def client():
    # Force DB init before running module tests
    init_db()
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    response = client.get("/api/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "healthy"]


def test_create_incident_bad_payload(client):
    # Short description (less than 10 chars)
    payload = {"incident_description": "Short", "analyst_name": "jdoe"}
    response = client.post("/api/incidents", json=payload)
    # Validation constraints block it
    assert response.status_code in [400, 422]


def test_create_incident_success(client):
    payload = {
        "incident_description": "Anomalous SSH connection attempts detected on database host.",
        "analyst_name": "test_analyst",
        "priority": "high",
    }
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["incident_id"] is not None
    assert data["priority"] == "high"
