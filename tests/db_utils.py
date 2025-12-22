# -*- coding: utf-8 -*-
"""
In-memory storage test utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains Rent-A-Bot tests storage utilities.

"""
from rentabot.models import Resource, resources_by_id, resources_by_name
import rentabot.models


def reset_database():
    """Clear all resources."""
    resources_by_id.clear()
    resources_by_name.clear()
    rentabot.models.next_resource_id = 1


def create_resources(qty):
    """ Create resources in memory.

    Args:
        qty: quantity of resources to create

    """
    for x in range(qty):
        resource = Resource(
            id=rentabot.models.next_resource_id,
            name="resource-{}".format(x),
            description="I'm the resource {}!".format(x)
        )
        resources_by_id[resource.id] = resource
        resources_by_name[resource.name] = resource
        rentabot.models.next_resource_id += 1


def create_resources_with_tags():
    """ Create resources with tags in memory

    """
    resources = {
        "arduino-1": "arduino leds",
        "arduino-2": "arduino motors",
        "raspberry-pi-1": "raspberry multipurpose",
        "raspberry-pi-2": "raspberry multipurpose"
    }
    for resource_name in list(resources):
        resource = Resource(
            id=rentabot.models.next_resource_id,
            name=resource_name,
            tags=resources[resource_name]
        )
        resources_by_id[resource.id] = resource
        resources_by_name[resource.name] = resource
        rentabot.models.next_resource_id += 1
