from datetime import date

from fastapi.testclient import TestClient

from billing_core.api.main import create_app


def test_create_plan_and_get() -> None:
    app = create_app()
    client = TestClient(app)

    payload = {
        "type": "flat",
        "code": "BIZ",
        "name": "Business",
        "currency": "EUR",
        "monthly_price": "99",
    }
    r = client.post("/plans", json=payload)
    assert r.status_code == 200
    assert r.json()["code"] == "BIZ"

    r2 = client.get("/plans/BIZ")
    assert r2.status_code == 200
    assert r2.json()["code"] == "BIZ"


def test_create_subscription_creates_invoice_for_paid_plan() -> None:
    app = create_app()
    client = TestClient(app)

    r = client.post(
        "/subscriptions",
        json={
            "customer_id": "cust_1",
            "plan_code": "PRO",
            "start_date": str(date(2026, 1, 1)),
            "seats": 1,
            "trial_days": 0,
            "period_days": 30,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["subscription"]["plan_code"] == "PRO"
    assert data["invoice_id"] is not None

    inv_id = data["invoice_id"]
    r2 = client.get(f"/invoices/{inv_id}")
    assert r2.status_code == 200
    inv = r2.json()
    assert inv["invoice_id"] == inv_id
    assert inv["total"]["currency"] == "EUR"
