"""Test fixtures.

v1's tests needed the real server running against a real MySQL database
with specific seed data, and ran at import time rather than under pytest.
Here every test gets a fresh SQLite file and a fixed "today", so tests are
isolated, repeatable and run in CI with no setup.
"""

from datetime import date

import pytest

from gaming_hub import create_app, db

TODAY = date(2026, 3, 1)


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}",
        "TODAY": lambda: TODAY,
        "LOAN_PERIOD_DAYS": 14,
    })
    db.create_schema(app)
    yield app
    app.extensions["db_engine"].dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def game(client):
    return client.post("/games", json={"title": "Galaxyfield", "platform": "PC", "genre": "RPG"}).get_json()


@pytest.fixture
def customer(client):
    return client.post("/customers", json={"name": "Amelia Barker", "email": "amelia@example.com"}).get_json()
