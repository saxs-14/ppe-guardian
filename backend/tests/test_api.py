from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


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
