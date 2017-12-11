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
        db.session.add(Resource(name="resource-{}".format(x),
                                description="I'm the resource {}!".format(x)))
    db.session.commit()


def create_resources_with_tags():
    """ Create resources with tags in the database

    """
    resources = {
        "arduino-1": "arduino leds",
        "arduino-2": "arduino motors",
        "raspberry-pi-1": "raspberry multipurpose",
        "raspberry-pi-2": "raspberry multipurpose"
    }
    for resource_name in list(resources):
        db.session.add(Resource(name=resource_name,
                                tags=resources[resource_name]))
    db.session.commit()
