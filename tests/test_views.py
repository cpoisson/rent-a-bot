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





