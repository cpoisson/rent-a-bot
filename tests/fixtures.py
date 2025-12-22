# -*- coding: utf-8 -*-
"""
Tests Fixtures
~~~~~~~~~~~~~~

This module contains Rent-A-Bot tests fixtures.

"""
import pytest
import rentabot


@pytest.fixture
def app(tmpdir):
    """Create and configure a test app instance."""
    rentabot.app.testing = True

    # Clear in-memory resources before each test
    rentabot.models.resources_by_id.clear()
    rentabot.models.resources_by_name.clear()
    rentabot.models.next_resource_id = 1

    yield rentabot.app.test_client()

    # Cleanup after test
    rentabot.models.resources_by_id.clear()
    rentabot.models.resources_by_name.clear()
    rentabot.models.next_resource_id = 1
