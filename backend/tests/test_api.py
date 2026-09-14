from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app, headers={"X-API-Key": settings.api_key})


def test_protected_endpoint_rejects_missing_key():
    anon = TestClient(app)
    r = anon.get("/api/dashboard/summary")
    assert r.status_code == 401


def test_dashboard_summary_shape():
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200
    for key in ["total_people_checked", "compliance_rate_pct", "non_compliant_events", "total_sessions"]:
        assert key in r.json()


def test_events_list_returns_array():
    r = client.get("/api/events")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_analyze_demo_runs_end_to_end():
    r = client.post("/api/analyze/demo", data={"zone": "construction"})
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        body = r.json()
        assert body["status"] == "completed"
        assert body["zone"] == "construction"
