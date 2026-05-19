import os
import sys

# Make backend/ importable so `from app.core.* import ...` resolves.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from fastapi.testclient import TestClient

from app.main import app as fastapi_app


@pytest.fixture(scope='session')
def client():
    # `with TestClient(...)` runs the FastAPI lifespan so the classifier loads/trains
    with TestClient(fastapi_app) as c:
        yield c
