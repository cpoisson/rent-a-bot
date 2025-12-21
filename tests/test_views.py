# -*- coding: utf-8 -*-

import pytest


def test_views_index(app):
    response = app.get('/')
    if response.status_code != 200:
        pytest.fail("Expected 200. Returned {}.".format(response))
