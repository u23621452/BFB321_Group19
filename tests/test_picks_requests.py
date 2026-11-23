"""Tests for confirming picks and sending material requests."""
from app.models import StockMovement


def pick(client, job, sku, qty):
    return client.post("/api/picks", json={"job_number": job, "sku": sku, "qty": qty})


def test_picks_need_operator_or_storeroom(client, login):
    assert pick(client, "J-2026-0430", "FST-M8", 1).status_code == 401
    login("reception")
    assert pick(client, "J-2026-0430", "FST-M8", 1).status_code == 403


def test_pick_takes_stock_out_and_updates_the_job(client, login):
    login("operator")
    response = pick(client, "J-2026-0430", "FST-M8", 10)
    assert response.status_code == 201
    assert response.json["on_hand_after"] == 590      # 600 - 10
    assert response.json["picked_total"] == 10
    assert response.json["remaining"] == 40           # job needs 50
    assert response.json["job_status"] == "kitting"


def test_pick_writes_a_ledger_row(app, client, login):
    login("operator")
    pick(client, "J-2026-0430", "FST-M8", 10)
    movement = StockMovement.query.one()
    assert movement.qty == -10
    assert movement.kind == "pick"


def test_picks_do_not_change_available_stock(client, login):
    login("operator")
    before = client.get("/api/inventory?search=fst-m8").json["items"][0]
    pick(client, "J-2026-0430", "FST-M8", 10)
    after = client.get("/api/inventory?search=fst-m8").json["items"][0]
    # the 10 boxes leave the shelf AND leave the reservation
    assert after["on_hand"] == before["on_hand"] - 10
    assert after["reserved"] == before["reserved"] - 10


def test_job_becomes_issued_when_every_line_is_picked(client, login):
    login("operator")
    pick(client, "J-2026-0430", "FST-M8", 50)
    pick(client, "J-2026-0430", "INS-PAPER", 2)
    last = pick(client, "J-2026-0430", "CBL-10MM", 10)
    assert last.json["job_status"] == "issued"
    assert client.get("/api/jobs/J-2026-0430").json["status"] == "issued"


def test_cannot_pick_more_than_the_job_needs(client, login):
    login("operator")
    response = pick(client, "J-2026-0430", "FST-M8", 51)
    assert response.status_code == 409


def test_cannot_pick_more_than_is_on_hand(client, login):
    login("operator")
    # 18 coils on hand; three jobs want 10 + 8 + 6
    assert pick(client, "J-2026-0437", "CU-WIND-01", 10).status_code == 201
    assert pick(client, "J-2026-0434", "CU-WIND-01", 8).status_code == 201
    response = pick(client, "J-2026-0431", "CU-WIND-01", 6)
    assert response.status_code == 409
    assert "on hand" in response.json["error"]["message"]


def test_pick_for_a_part_not_on_the_bom_is_refused(client, login):
    login("operator")
    response = pick(client, "J-2026-0430", "CU-WIND-01", 1)
    assert response.status_code == 422
    assert "sku" in response.json["error"]["details"]


def test_pick_for_unknown_job_is_404(client, login):
    login("operator")
    assert pick(client, "J-2026-9999", "FST-M8", 1).status_code == 404


def test_pick_rejects_bad_quantity(client, login):
    login("operator")
    assert pick(client, "J-2026-0430", "FST-M8", 0).status_code == 422
    assert pick(client, "J-2026-0430", "FST-M8", "abc").status_code == 422


def test_operator_can_send_a_material_request(client, login):
    login("operator")
    response = client.post("/api/requests", json={
        "sku": "CU-WIND-01", "qty": 3, "note": "Extra for rework"})
    assert response.status_code == 201
    assert response.json["status"] == "open"


def test_request_needs_valid_item_and_quantity(client, login):
    login("operator")
    response = client.post("/api/requests", json={"sku": "NOPE", "qty": 0})
    assert response.status_code == 422
    assert set(response.json["error"]["details"]) == {"sku", "qty"}


def test_storeroom_sees_the_requests_but_operator_does_not(client, login):
    login("operator")
    client.post("/api/requests", json={"sku": "FST-M8", "qty": 5})
    assert client.get("/api/requests").status_code == 403

    login("storeroom")
    data = client.get("/api/requests?status=open").json
    assert data["total"] == 1
    assert data["items"][0]["sku"] == "FST-M8"


def test_kpis_count_picks_and_requests(client, login):
    login("operator")
    pick(client, "J-2026-0430", "FST-M8", 10)
    client.post("/api/requests", json={"sku": "FST-M8", "qty": 5})
    data = client.get("/api/kpis").json
    assert data["picks_today"] == 1
    assert data["open_requests"] == 1