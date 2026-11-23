"""Tests for login and the inventory endpoint."""


def test_inventory_needs_login(client):
    response = client.get("/api/inventory")
    assert response.status_code == 401
    assert response.json["error"]["code"] == 401


def test_login_with_wrong_password_fails(login):
    response = login("reception", password="wrong")
    assert response.status_code == 401


def test_login_with_missing_fields_fails(client):
    response = client.post("/api/auth/login", json={"email": "x"})
    assert response.status_code == 400


def test_login_works_and_me_shows_role(client, login):
    assert login("storeroom").status_code == 200
    me = client.get("/api/auth/me")
    assert me.json["role"] == "storeroom"


def test_logout_blocks_access_again(client, login):
    login("reception")
    client.post("/api/auth/logout")
    assert client.get("/api/inventory").status_code == 401


def test_inventory_is_paginated(client, login):
    login("reception")
    data = client.get("/api/inventory?per_page=3&page=2").json
    assert data["total"] == 8          # 8 products in the seed data
    assert data["pages"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 2


def test_inventory_filter_by_status(client, login):
    login("reception")
    data = client.get("/api/inventory?status=critical").json
    assert data["total"] > 0
    assert all(row["status"] == "critical" for row in data["items"])


def test_inventory_search_by_sku(client, login):
    login("reception")
    data = client.get("/api/inventory?search=cu-wind").json
    assert [row["sku"] for row in data["items"]] == ["CU-WIND-01"]


def test_inventory_shows_reserved_and_available(client, login):
    login("reception")
    row = client.get("/api/inventory?search=cu-wind").json["items"][0]
    # 18 on hand, but open jobs have promised more than that
    assert row["on_hand"] == 18
    assert row["reserved"] == 24
    assert row["available"] == 0


def test_inventory_rejects_bad_status(client, login):
    login("reception")
    response = client.get("/api/inventory?status=banana")
    assert response.status_code == 400


def test_inventory_rejects_bad_page_number(client, login):
    login("reception")
    assert client.get("/api/inventory?page=abc").status_code == 400