"""Tests for the web pages (login, redirects and the dashboard shell)."""


def test_home_sends_visitors_to_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_login_page_opens(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"StockFlow Engine" in response.data


def test_dashboard_needs_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_every_role_can_open_the_dashboard(client, login):
    for role in ("reception", "storeroom", "operator", "admin"):
        login(role)
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert b"Welcome" in response.data


def test_logged_in_user_skips_the_login_page(client, login):
    login("reception")
    response = client.get("/login")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_menu_shows_the_name_and_role(client, login):
    login("storeroom")
    page = client.get("/dashboard").data
    assert b"Sam Storeroom" in page
    assert b"storeroom" in page


def test_static_files_are_served(client):
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/static/js/api.js").status_code == 200


def test_open_filter_hides_issued_jobs(client, login):
    login("operator")
    data = client.get("/api/jobs?open=1&per_page=20").json
    assert data["total"] == 8                 # 9 jobs, one is issued
    assert all(job["status"] != "issued" for job in data["items"])