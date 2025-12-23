"""
In-memory storage test utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains Rent-A-Bot tests storage utilities.

"""

import rentabot.models
from rentabot.models import Resource, resources_by_id


def reset_database():
    """Clear all resources."""
    resources_by_id.clear()
    rentabot.models.next_resource_id = 1


def create_resources(qty):
    """Create resources in memory.

    Args:
        qty: quantity of resources to create

    """
    for x in range(qty):
        resource = Resource(
            id=rentabot.models.next_resource_id,
            name=f"resource-{x}",
            description=f"I'm the resource {x}!",
        )
        resources_by_id[resource.id] = resource
        rentabot.models.next_resource_id += 1


def create_resources_with_tags():
    """Create resources with tags in memory"""
    resources = {
        "arduino-1": "arduino leds",
        "arduino-2": "arduino motors",
        "raspberry-pi-1": "raspberry multipurpose",
        "raspberry-pi-2": "raspberry multipurpose",
    }
    for resource_name in list(resources):
        resource = Resource(
            id=rentabot.models.next_resource_id, name=resource_name, tags=resources[resource_name]
        )
        resources_by_id[resource.id] = resource
        rentabot.models.next_resource_id += 1
