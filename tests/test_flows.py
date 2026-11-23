"""Integration tests: each test walks through a whole business flow, switching
between roles the way real people would, to prove the pieces work together."""
from datetime import date, timedelta


def job_body(sku, qty, days=1):
    return {
        "customer": "Flow Test Customer",
        "description": "Integration test job",
        "start_date": (date.today() + timedelta(days=days)).isoformat(),
        "priority": "Urgent",
        "lines": [{"sku": sku, "qty": qty}],
    }


def kpis(client):
    return client.get("/api/kpis").json


def test_flow_1_reception_opens_a_job_and_stock_is_reserved(client, login):
    login("reception")
    before = kpis(client)

    created = client.post("/api/jobs", json=job_body("GSKT-EPDM", 2))
    assert created.status_code == 201
    number = created.json["job_number"]
    assert created.json["status"] == "reserved"

    # the new job can be found, opened and counted
    found = client.get("/api/jobs?search=Flow Test").json
    assert [j["job_number"] for j in found["items"]] == [number]
    assert client.get("/api/jobs/" + number).json["lines"][0]["sku"] == "GSKT-EPDM"
    assert kpis(client)["open_jobs"] == before["open_jobs"] + 1
    assert kpis(client)["reserved_lines"] == before["reserved_lines"] + 1

    # the inventory page sees the reservation straight away
    gasket = client.get("/api/inventory?search=gskt").json["items"][0]
    assert gasket["reserved"] == 22      # 20 already reserved + 2 new


def test_flow_2_a_shortage_reaches_the_storeroom_queue(client, login):
    login("reception")
    before = kpis(client)["shortage_jobs"]
    number = client.post("/api/jobs", json=job_body("GSKT-EPDM", 500)).json["job_number"]
    assert client.get("/api/jobs/" + number).json["status"] == "shortage"
    # it starts first, so it also pushes a later gasket job into shortage
    assert kpis(client)["shortage_jobs"] > before

    # the storeroom logs in and sees the job and the order alert
    login("storeroom")
    queue = client.get("/api/queue?days=7").json
    assert number in [j["job_number"] for j in queue["jobs"]]
    alert = next(r for r in queue["shortage_summary"] if r["sku"] == "GSKT-EPDM")
    assert alert["short_by"] > 0
    assert alert["recommended_order_qty"] >= alert["short_by"]
    assert alert["order_by"] is not None


def test_flow_3_operator_picks_a_job_and_the_ledger_updates(client, login):
    login("reception")
    number = client.post("/api/jobs", json=job_body("GSKT-EPDM", 5)).json["job_number"]

    login("operator")
    on_hand = client.get("/api/inventory?search=gskt").json["items"][0]["on_hand"]
    result = client.post("/api/picks", json={"job_number": number, "sku": "GSKT-EPDM", "qty": 5})
    assert result.status_code == 201
    assert result.json["job_status"] == "issued"       # its only line is done

    # stock went down, the job left the open list, the KPIs moved
    gasket = client.get("/api/inventory?search=gskt").json["items"][0]
    assert gasket["on_hand"] == on_hand - 5
    open_numbers = [j["job_number"] for j in client.get("/api/jobs?open=1&per_page=100").json["items"]]
    assert number not in open_numbers
    assert kpis(client)["picks_today"] == 1

    # a finished job cannot be picked again
    again = client.post("/api/picks", json={"job_number": number, "sku": "GSKT-EPDM", "qty": 1})
    assert again.status_code == 409


def test_material_request_goes_from_operator_to_storeroom(client, login):
    login("operator")
    sent = client.post("/api/requests", json={"sku": "FST-M8", "qty": 3, "note": "dropped some"})
    assert sent.status_code == 201

    login("storeroom")
    rows = client.get("/api/requests?status=open").json["items"]
    assert [(r["sku"], r["qty"]) for r in rows] == [("FST-M8", 3)]
    assert kpis(client)["open_requests"] == 1


def test_every_error_uses_the_same_json_shape(client, login):
    login("reception")
    for url in ("/api/jobs/J-2026-9999", "/api/nothing-here"):
        body = client.get(url).json
        assert set(body["error"]) >= {"code", "message"}
    bad = client.post("/api/jobs", json={})
    assert bad.status_code == 422 and "details" in bad.json["error"]


def test_logging_out_closes_the_api(client, login):
    login("reception")
    assert client.get("/api/kpis").status_code == 200
    client.post("/api/auth/logout")
    assert client.get("/api/kpis").status_code == 401



def test_reception_can_change_a_job(client, login):
    login("reception")
    number = client.post("/api/jobs", json=job_body("GSKT-EPDM", 2)).json["job_number"]

    changed = client.patch("/api/jobs/" + number,
                           json={"priority": "Normal", "description": "Changed by test"})
    assert changed.status_code == 200
    assert changed.json["priority"] == "Normal"

    # the change was saved, not just echoed back
    again = client.get("/api/jobs/" + number).json
    assert again["description"] == "Changed by test"
    assert again["customer"] == "Flow Test Customer"       # untouched


def test_moving_a_job_later_frees_stock_for_the_others(client, login):
    login("reception")
    before = kpis(client)["shortage_jobs"]
    number = client.post("/api/jobs", json=job_body("GSKT-EPDM", 500)).json["job_number"]
    while_first = kpis(client)["shortage_jobs"]
    assert while_first > before          # it starts first, so it pushes later jobs short

    later = (date.today() + timedelta(days=60)).isoformat()
    moved = client.patch("/api/jobs/" + number, json={"start_date": later})
    assert moved.status_code == 200

    # now the earlier jobs are served first, so fewer jobs are short
    assert kpis(client)["shortage_jobs"] < while_first


def test_job_update_is_checked_and_protected(client, login):
    login("reception")
    number = client.post("/api/jobs", json=job_body("GSKT-EPDM", 2)).json["job_number"]
    url = "/api/jobs/" + number

    past = (date.today() - timedelta(days=1)).isoformat()
    bad = client.patch(url, json={"start_date": past, "priority": "Low", "colour": "red"})
    assert bad.status_code == 422
    assert set(bad.json["error"]["details"]) == {"start_date", "priority", "colour"}

    assert client.patch(url, json={}).status_code == 422
    assert client.patch("/api/jobs/J-2026-9999", json={"priority": "Normal"}).status_code == 404

    login("operator")
    assert client.patch(url, json={"priority": "Normal"}).status_code == 403


def test_an_issued_job_cannot_be_changed(client, login):
    login("reception")
    number = client.post("/api/jobs", json=job_body("GSKT-EPDM", 5)).json["job_number"]
    login("operator")
    client.post("/api/picks", json={"job_number": number, "sku": "GSKT-EPDM", "qty": 5})

    login("reception")
    result = client.patch("/api/jobs/" + number, json={"priority": "Normal"})
    assert result.status_code == 409


def test_storeroom_can_close_a_material_request(client, login):
    login("operator")
    request_id = client.post("/api/requests",
                             json={"sku": "FST-M8", "qty": 3}).json["id"]

    login("storeroom")
    assert kpis(client)["open_requests"] == 1
    done = client.patch("/api/requests/" + str(request_id), json={"status": "done"})
    assert done.status_code == 200 and done.json["status"] == "done"

    # it leaves the open list and the dashboard number drops
    assert client.get("/api/requests?status=open").json["items"] == []
    assert kpis(client)["open_requests"] == 0


def test_request_update_is_checked_and_protected(client, login):
    login("operator")
    request_id = client.post("/api/requests",
                             json={"sku": "FST-M8", "qty": 3}).json["id"]
    url = "/api/requests/" + str(request_id)
    assert client.patch(url, json={"status": "done"}).status_code == 403   # operators cannot close

    login("storeroom")
    assert client.patch(url, json={"status": "banana"}).status_code == 422
    assert client.patch("/api/requests/9999", json={"status": "done"}).status_code == 404
    assert client.patch("/api/requests/abc", json={"status": "done"}).status_code == 404



def test_a_database_conflict_becomes_a_clean_409(client, login, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    def clash(*args, **kwargs):
        raise IntegrityError("INSERT", {}, Exception("duplicate entry"))

    monkeypatch.setattr("app.services.jobs.create_job", clash)
    login("reception")
    result = client.post("/api/jobs", json=job_body("GSKT-EPDM", 2))
    assert result.status_code == 409
    assert result.json["error"]["code"] == 409


def test_an_unexpected_error_hides_the_details(client, login, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr("app.services.jobs.create_job", broken)
    login("reception")
    result = client.post("/api/jobs", json=job_body("GSKT-EPDM", 2))
    assert result.status_code == 500
    assert "secret" not in result.get_data(as_text=True)