# -*- coding: utf-8 -*-
"""
Database test utilities
~~~~~~~~~~~~~~~~~~~~~~~

This module contains Rent-A-Bot tests database utilities.

"""
from rentabot.models import Resource, db


def reset_database():
    """Drop and create tables."""
    # Reset database
    db.drop_all()

    # Create tables
    db.create_all()


def create_resources(qty):
    """ Create resources in the database.

    Args:
        qty: quantity of resources to create

    """
    for x in range(qty):
        db.session.add(Resource(name="resource_{}".format(x),
                                description="I'm the resource {}!".format(x)))
    db.session.commit()
