from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200


def test_root_lists_zones():
    r = client.get("/")
    assert "construction" in r.json()["zones"]
