from fastapi.testclient import TestClient
from foodflow.api import app
from foodflow.data import generate_demo_orders

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_demo_analysis():
    response = client.get("/demo-analysis")
    assert response.status_code == 200
    assert response.json()["kpis"]["total_orders"] == 1200


def test_post_analyze():
    rows = generate_demo_orders(12).to_dict(orient="records")
    response = client.post("/analyze", json={"orders": rows})
    assert response.status_code == 200
    assert response.json()["kpis"]["total_orders"] == 12


def test_reject_bad_payload():
    response = client.post("/analyze", json={"orders": [{"order_id": "x"}]})
    assert response.status_code == 422
