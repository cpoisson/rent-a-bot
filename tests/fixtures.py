"""
Tests Fixtures
~~~~~~~~~~~~~~

This module contains Rent-A-Bot tests fixtures.

"""

import pytest
from fastapi.testclient import TestClient

import rentabot.models


@pytest.fixture
def app(tmpdir):
    """Create and configure a test app instance."""
    # Import FastAPI app
    from rentabot.main import app as fastapi_app

    # Clear in-memory resources before each test
    rentabot.models.resources_by_id.clear()
    rentabot.models.resources_by_name.clear()
    rentabot.models.next_resource_id = 1

    yield TestClient(fastapi_app)

    # Cleanup after test
    rentabot.models.resources_by_id.clear()
    rentabot.models.resources_by_name.clear()
    rentabot.models.next_resource_id = 1
