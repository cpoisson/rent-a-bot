# -*- coding: utf-8 -*-
"""
rentabot.controllers
~~~~~~~~~~~~~~~~~~~~

This module contains rent-a-bot functions related to database manipulation.
"""


from rentabot.models import Resource, db
from rentabot.exceptions import ResourceAlreadyLocked, ResourceAlreadyUnlocked, InvalidLockToken
from uuid import uuid4
import yaml


def lock_resource(resource):
    """Lock resource. Raise an exception if the resource is already locked.

    Args:
        resource (Resource): The resource to lock.

    Returns:
        A lock token
    """
    if resource.lock_token is not None:
        raise ResourceAlreadyLocked
    else:
        resource.lock_token = str(uuid4())
        resource.lock_details = u'Resource locked.'
        db.session.commit()
    return resource.lock_token


def unlock_resource(resource, lock_token):
    """Unlock resource. Raise an exception if the token is invalid or if the resource is already unlocked.

    Args:
        resource (Resource): The resource to unlock.
        lock_token (str): The lock token to authorize the unlock.

    Returns:
        None
    """
    if resource.lock_token is None:
        raise ResourceAlreadyUnlocked
    elif lock_token != resource.lock_token:
        raise InvalidLockToken
    else:
        resource.lock_token = None
        resource.lock_details = u'Resource available.'
        db.session.commit()


def populate_database_from_file(resource_file):
    """ Populate the database using the resources described in a yaml file.

    Args:
      resource_file (str): the resource descriptor.

    """
    with open(resource_file, "r") as f:
        resources = yaml.load(f)

    if len(list(resources)) == 0:
        msg = "The resource descriptor does not contain any resources: {}".format(resource_file)
        raise Exception(msg)

    if len(list(resources)) != len(set(list(resources))):
        msg = "The resource descriptor contains duplicated resource names. {}".format(resource_file)
        raise Exception(msg)

    db.drop_all()
    db.create_all()

    for resource_name in list(resources):

        try:
            description = resources[resource_name]['description']
        except KeyError:
            description = None

        try:
            endpoint = resources[resource_name]['endpoint']
        except KeyError:
            endpoint = None

        try:
            tags = resources[resource_name]['tags']
        except KeyError:
            tags = None

        db.session.add(Resource(resource_name,
                                description=description,
                                endpoint=endpoint,
                                tags=tags))
        db.session.commit()

