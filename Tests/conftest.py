import pytest

import seed
from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    """A fresh app with a throw-away database, filled with the demo data."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        users = seed.add_users()
        products = seed.add_products()
        seed.add_jobs(products, users["reception"])
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    """Call login('storeroom') to log the test client in as that role."""
    def do(role="reception", password="Password123"):
        return client.post("/api/auth/login", json={
            "email": role + "@stockflow.test", "password": password})
    return do