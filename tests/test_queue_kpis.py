"""Tests for the storeroom queue and the dashboard KPIs."""

SEVEN_DAY_JOBS = ["J-2026-0430", "J-2026-0431", "J-2026-0432",
                  "J-2026-0433", "J-2026-0434", "J-2026-0435"]


def test_queue_needs_the_right_role(client, login):
    assert client.get("/api/queue").status_code == 401
    login("operator")
    assert client.get("/api/queue").status_code == 403


def test_queue_shows_jobs_starting_within_7_days(client, login):
    login("storeroom")
    data = client.get("/api/queue?days=7").json
    assert [j["job_number"] for j in data["jobs"]] == SEVEN_DAY_JOBS
    assert data["window_days"] == 7


def test_queue_alerts_about_a_shortage_inside_the_window(client, login):
    login("storeroom")
    summary = client.get("/api/queue?days=7").json["shortage_summary"]
    assert [row["sku"] for row in summary] == ["PCB-PSU-12"]
    pcb = summary[0]
    # 20 boards on hand, 10 go to J-2026-0432, so 10 are left for a job needing 15
    assert pcb["short_by"] == 5
    # model: EOQ 79.6 -> rounded up to a pack size of 10 -> 80
    assert pcb["recommended_order_qty"] == 80
    # 18 day lead time but the job starts in 6 days, so normal ordering is too late
    assert pcb["expedite"] is True


def test_queue_14_day_window_finds_more_shortages(client, login):
    login("storeroom")
    data = client.get("/api/queue?days=14").json
    assert len(data["jobs"]) == 8
    skus = {row["sku"] for row in data["shortage_summary"]}
    assert skus == {"PCB-PSU-12", "TX-CORE-03", "CU-WIND-01",
                    "SM-STL-2MM", "FST-M8"}


def test_queue_order_dates_use_the_lead_time(client, login):
    login("storeroom")
    rows = client.get("/api/queue?days=14").json["shortage_summary"]
    steel = next(r for r in rows if r["sku"] == "SM-STL-2MM")
    # needed in 9 days, lead time 7 days: there is still time to order
    assert steel["expedite"] is False
    assert steel["recommended_order_qty"] == 80


def test_queue_rejects_bad_days(client, login):
    login("storeroom")
    for bad in ("0", "31", "abc"):
        assert client.get("/api/queue?days=" + bad).status_code == 400


def test_kpis_need_login(client):
    assert client.get("/api/kpis").status_code == 401


def test_kpis_match_the_seed_data(client, login):
    login("reception")
    data = client.get("/api/kpis").json
    assert data["open_jobs"] == 8          # 9 jobs, one already issued
    assert data["shortage_jobs"] == 3
    assert data["shortage_items"] == 5
    assert data["reserved_lines"] == 25
    assert data["upcoming_7_days"] == 6
    assert data["critical_items"] == 6
    assert data["low_items"] == 1
    assert data["open_requests"] == 0
    assert data["picks_today"] == 0