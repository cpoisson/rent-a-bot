# -*- coding: utf-8 -*-
"""
rentabot.models
~~~~~~~~~~~~~~~

This module contains rent-a-bot database model.
"""


from rentabot import app
from flask_sqlalchemy import SQLAlchemy
import os

# Set database
db_path = '/tmp/rent-a-bot.sqlite'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Resource(db.Model):
    """ Resource class.

    """
    id = db.Column(db.Integer, primary_key=True)            # Id
    name = db.Column(db.String(80), unique=True)            # Unique Resource name
    description = db.Column(db.String(160))                 # Resource description
    lock_token = db.Column(db.String(80))                   # Resource lock token
    lock_details = db.Column(db.String(160))                # Resource lock details
    endpoint = db.Column(db.String(160))                    # Resource endpoint (e.g. an IP address)
    tags = db.Column(db.String(160))                        # Resource tags

    def __init__(self, name, endpoint=None, description=None, tags=None):
        self.name = name
        self.description = description
        self.lock_details = u'Resource is available'
        self.endpoint = endpoint
        self.tags = tags

    @property
    def dict(self):
        rv = dict()
        rv['id'] = self.id
        rv['name'] = self.name
        rv['description'] = self.description
        rv['lock-token'] = self.lock_token
        rv['lock-details'] = self.lock_details
        rv['endpoint'] = self.endpoint
        rv['tags'] = self.tags
        return rv

