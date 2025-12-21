# -*- coding: utf-8 -*-
"""
Tests Configuration
~~~~~~~~~~~~~~~~~~~

This module contains pytest configuration and shared fixtures.

"""
import pytest
import rentabot
import os


@pytest.fixture
def app(tmpdir):
    """Create and configure a test app instance."""
    rentabot.app.testing = True

    # Use pytest tmpdir for a temp database path
    db_path = os.path.join(tmpdir.strpath, 'rent-a-bot.sqlite')
    rentabot.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
    rentabot.models.db_path = db_path

    # Create database tables within app context
    with rentabot.app.app_context():
        rentabot.models.db.create_all()
        rentabot.models.db.session.commit()

    yield rentabot.app.test_client()

    # Cleanup
    with rentabot.app.app_context():
        rentabot.models.db.session.remove()
        rentabot.models.db.drop_all()
