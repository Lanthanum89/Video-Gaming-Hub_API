"""Video Gaming Hub API, v2.

Application factory: build the app from config instead of creating a global
`app` at import time, so tests can spin up an isolated instance per test.
"""

from datetime import date

from flask import Flask

from . import cli, db, errors
from .api import bp as api_bp
from .config import Config


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    # The clock is injectable so "overdue" logic can be tested deterministically.
    app.config.setdefault("TODAY", date.today)
    if overrides:
        app.config.update(overrides)

    db.init_app(app)
    errors.register(app)
    cli.register(app)
    app.register_blueprint(api_bp)
    return app
