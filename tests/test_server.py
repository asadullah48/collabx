from fastapi.testclient import TestClient
from collabx.server import app

client = TestClient(app)

def test_server_dashboard_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "CollabX" in res.text

def test_server_healthz():
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_server_readyz():
    res = client.get("/readyz")
    assert res.status_code == 200
    assert res.json()["editorial_team_agents_active"] == 3

def test_server_produce_newsletter_api():
    payload = {
        "brief_id": "BRIEF-TEST-01",
        "topic": "Autonomous AI Agent Swarms",
        "target_audience": "Tech Leaders",
        "tone": "TECH_PIONEER",
        "target_word_count": 600
    }
    res = client.post("/api/v1/editorial/produce-newsletter", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "The Next Frontier:" in data["title"]
    assert data["feedback"]["fact_check_passed"] is True
