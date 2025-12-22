# -*- coding: utf-8 -*-
""" Rent-A-Bot

Your automation resource provider.
"""

import os
from flask import Flask

# Create Flask app
app = Flask(__name__)

# Import logger first (no dependencies)
from rentabot.logger import get_logger
logger = get_logger(__name__)

# Import models (depends on app)
import rentabot.models

# Import controllers and views (depend on models)
import rentabot.controllers
import rentabot.views


def init_app():
    """Initialize the application resources."""
    # Init the resources from a file descriptor if the env variable is set
    try:
        rentabot.controllers.populate_database_from_file(os.environ['RENTABOT_RESOURCE_DESCRIPTOR'])
    except KeyError:
        logger.info("No RENTABOT_RESOURCE_DESCRIPTOR environment variable set, starting with empty resources")


# Only initialize if running as main app (not during testing)
if os.environ.get('FLASK_APP') == 'rentabot':
    init_app()
