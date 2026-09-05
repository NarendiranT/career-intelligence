from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

from backend.db import engine
from mcp.registry import tools


@pytest.fixture
def sample_resume() -> Path:
    return Path(__file__).parent / "fixtures" / "sample_resume.txt"


@pytest.fixture
def sample_jd() -> Path:
    return Path(__file__).parent / "fixtures" / "sample_jd.txt"


def postgres_available() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


requires_postgres = pytest.mark.skipif(not postgres_available(), reason="postgres is not running")


@pytest.fixture
def db_user():
    if not postgres_available():
        pytest.skip("postgres is not running")
    user_id = uuid.uuid4()
    tools.invoke("create_or_update_user", user_id=user_id, email=f"{user_id}@example.com")
    yield user_id
