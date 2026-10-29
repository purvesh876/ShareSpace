import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient

# Ensure test environment settings are active
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "false"

from app.main import app


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
