# -*- coding: utf-8 -*-
""" Rent-A-Bot

Your automation resource provider.
"""

import os
from flask import Flask
app = Flask(__name__)

import rentabot.views
import rentabot.models
import rentabot.controllers


# Delete the database if the file exists
if os.path.exists(rentabot.models.db_path):
    os.remove(rentabot.models.db_path)

# Create the database
rentabot.models.db.create_all()
rentabot.models.db.session.commit()

# Init the database from a file descriptor is the env variable is set
try:
    rentabot.controllers.populate_database_from_file(os.environ['RENTABOT_RESOURCE_DESCRIPTOR'])
except KeyError:
    pass
