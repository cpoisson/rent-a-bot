# -*- coding: utf-8 -*-
"""
Tests Fixtures
~~~~~~~~~~~~~~

This module contains Rent-A-Bot tests fixtures.

"""
import pytest
import rentabot
import os


@pytest.fixture
def app(tmpdir):
    rentabot.app.testing = True
    # Use pytest tmpdir for a temp database path
    rentabot.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(tmpdir.strpath, 'rent-a-bot.sqlite')
    return rentabot.app.test_client()