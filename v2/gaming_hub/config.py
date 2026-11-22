"""Configuration from environment variables.

v1 kept credentials in a committed `config.py`. Environment variables keep
secrets out of the repo entirely, and the same code runs locally, in CI and
in production with different settings.
"""

import os


class Config:
    # SQLite by default so the project runs with zero setup.
    # MySQL example: mysql+mysqlconnector://user:password@localhost/video_gaming_hub
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///gaming_hub.db")
    LOAN_PERIOD_DAYS = int(os.environ.get("LOAN_PERIOD_DAYS", "14"))
