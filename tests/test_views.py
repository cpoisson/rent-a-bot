
import pytest


def test_views_index(app):
    response = app.get("/")
    if response.status_code != 200:
        pytest.fail(f"Expected 200. Returned {response}.")
