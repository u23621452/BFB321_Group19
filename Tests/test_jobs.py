"""Tests for the jobs endpoints: list, detail and creating a job."""
from datetime import date, timedelta


def new_job(**changes):
    """A valid job that starts well after the seeded jobs, so it is last in
    the queue for stock. Pass keyword arguments to change a field."""
    job = {
        "customer": "Test Customer",
        "description": "Test assembly",
        "start_date": (date.today() + timedelta(days=30)).isoformat(),
        "priority": "Normal",
        "lines": [{"sku": "GSKT-EPDM", "qty": 5}],
    }
    job.update(changes)
    return job


def test_jobs_need_login(client):
    assert client.get("/api/jobs").status_code == 401


def test_job_list_is_paginated(client, login):
    login("reception")
    data = client.get("/api/jobs?per_page=4&page=3").json
    assert data["total"] == 9           # 9 jobs in the seed data
    assert data["pages"] == 3
    assert len(data["items"]) == 1      # 9 jobs, 4 per page: last page has 1


def test_job_list_filters_by_status(client, login):
    login("reception")
    data = client.get("/api/jobs?status=shortage").json
    assert data["total"] == 3
    assert all(job["status"] == "shortage" for job in data["items"])


def test_job_list_searches_customer(client, login):
    login("storeroom")
    data = client.get("/api/jobs?search=kopano").json
    assert data["total"] == 2


def test_job_list_rejects_bad_status(client, login):
    login("reception")
    assert client.get("/api/jobs?status=banana").status_code == 400


def test_job_detail_shows_shortage(client, login):
    login("operator")
    job = client.get("/api/jobs/J-2026-0437").json
    assert job["status"] == "shortage"
    shortage = {s["sku"]: s for s in job["shortages"]}
    # needs 10 coils but only 4 are left after the earlier jobs took theirs
    assert shortage["CU-WIND-01"]["required"] == 10
    assert shortage["CU-WIND-01"]["free"] == 4
    assert shortage["CU-WIND-01"]["short_by"] == 6


def test_job_detail_not_found(client, login):
    login("reception")
    response = client.get("/api/jobs/J-2026-9999")
    assert response.status_code == 404


def test_reception_can_create_job_and_stock_is_reserved(client, login):
    login("reception")
    response = client.post("/api/jobs", json=new_job())
    assert response.status_code == 201
    assert response.json["job_number"].endswith("0438")   # seed ends at 0437
    assert response.json["status"] == "reserved"

    gasket = client.get("/api/inventory?search=gskt").json["items"][0]
    assert gasket["reserved"] == 25     # 20 already reserved + 5 new


def test_job_with_too_few_parts_is_marked_shortage(client, login):
    login("reception")
    job = new_job(lines=[{"sku": "GSKT-EPDM", "qty": 50}])
    response = client.post("/api/jobs", json=job)
    assert response.status_code == 201
    assert response.json["status"] == "shortage"
    # 30 on hand, 20 promised to other jobs -> 10 free -> short by 40
    assert response.json["shortages"][0]["short_by"] == 40


def test_only_reception_can_create_jobs(client, login):
    login("storeroom")
    assert client.post("/api/jobs", json=new_job()).status_code == 403


def test_create_job_reports_every_problem(client, login):
    login("reception")
    bad = new_job(customer="A", description="",
                  start_date="2020-01-01", lines=[{"sku": "NOPE", "qty": 1}])
    response = client.post("/api/jobs", json=bad)
    assert response.status_code == 422
    details = response.json["error"]["details"]
    assert set(details) == {"customer", "description", "start_date", "lines"}


def test_create_job_rejects_duplicate_and_zero_quantity(client, login):
    login("reception")
    twice = new_job(lines=[{"sku": "GSKT-EPDM", "qty": 1},
                           {"sku": "GSKT-EPDM", "qty": 2}])
    assert client.post("/api/jobs", json=twice).status_code == 422
    zero = new_job(lines=[{"sku": "GSKT-EPDM", "qty": 0}])
    assert client.post("/api/jobs", json=zero).status_code == 422


def test_create_job_rejects_empty_body(client, login):
    login("reception")
    assert client.post("/api/jobs", json={}).status_code == 422