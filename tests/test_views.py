# -*- coding: utf-8 -*-

import pytest
import rentabot


@pytest.fixture
def app():
    rentabot.app.testing = True
    return rentabot.app.test_client()


def test_views_index(app):
    response = app.get('/')
    if response.status_code != 200:
        pytest.fail("Expected 200. Returned {}.".format(response))


def test_get_resources_empty(app):
    response = app.get('/rentabot/api/v1.0/resources')
    if response.status_code != 200:
        pytest.fail("Expected to return 200. Returned {}.".format(response))


def test_get_resource_id_does_not_exist(app):
    response = app.get('/rentabot/api/v1.0/ressources/3000')
    if response.status_code != 404:
        pytest.fail("Expected to return 404. Returned {}.".format(response))



