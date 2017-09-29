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
    endpoint = db.Column(db.String(160))                    # Resource endpoint (e.g. an IP address)
    description = db.Column(db.String(160))                 # Resource description
    tags = db.Column(db.String(160))                        # Resource tags
    status = db.Column(db.Integer)                          # Resource Status
    status_details = db.Column(db.String(160))              # Resource Status Details
    lock_key = db.Column(db.String(80))                     # Resource lock key

    STATUS = {u'available': 0, u'locked': 1}

    def __init__(self, name, endpoint=None, description=None, tags=None):
        self.name = name
        self.endpoint = endpoint
        self.description = description
        self.tags = tags
        self.status = self.STATUS['available']
        self.status_details = u'Resource available.'

    @property
    def dict(self):
        resource = {
            'id': self.id,
            'name': self.name,
            'endpoint': self.endpoint,
            'description': self.description,
            'tags': self.tags,
            'status': self.status,
            'status_details': self.status_details,
            'lock_key': self.lock_key
        }
        return resource

    def __repr__(self):
        return str(self.dict)


# Create database if the file does not exist
if not os.path.exists(db_path):
    db.create_all()
    db.session.commit()
