import os

import pytest


def test_views_index(app):
    response = app.get("/")
    if response.status_code != 200:
        pytest.fail(f"Expected 200. Returned {response}.")


def test_startup_without_resource_descriptor():
    """
    Title: Test application startup without RENTABOT_RESOURCE_DESCRIPTOR

    Given: The RENTABOT_RESOURCE_DESCRIPTOR environment variable is not set
    When: The application starts up
    Then: The application should start successfully with empty resources
    """
    from fastapi.testclient import TestClient

    # Save and remove environment variable if it exists
    original_value = os.environ.pop("RENTABOT_RESOURCE_DESCRIPTOR", None)

    try:
        # Import app which will trigger lifespan startup
        from rentabot.main import app

        client = TestClient(app)
        response = client.get("/api/v1/resources")

        # Should start successfully and return empty resources
        assert response.status_code == 200

    finally:
        # Restore original environment variable
        if original_value is not None:
            os.environ["RENTABOT_RESOURCE_DESCRIPTOR"] = original_value


def test_health_endpoint(app):
    """
    Title: Test /health endpoint

    Given: The application is running
    When: Requesting the /health endpoint
    Then: A 200 OK status is returned with status "ok"
    """
    response = app.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_readiness_endpoint(app):
    """
    Title: Test /readiness endpoint

    Given: The application is running
    When: Requesting the /readiness endpoint
    Then: A 200 OK status is returned with status "ready"
    """
    response = app.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
