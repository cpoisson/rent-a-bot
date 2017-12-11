# -*- coding: utf-8 -*-
"""
rentabot.controllers
~~~~~~~~~~~~~~~~~~~~

This module contains rent-a-bot functions related to database manipulation.
"""


from rentabot.models import Resource, db
from rentabot.exceptions import ResourceException, ResourceNotFound
from rentabot.exceptions import ResourceAlreadyLocked, ResourceAlreadyUnlocked, InvalidLockToken
from rentabot.exceptions import ResourceDescriptorIsEmpty
from rentabot.logger import get_logger

from uuid import uuid4
import yaml

import threading
thread_safe_lock = threading.Lock()

logger = get_logger(__name__)


def get_all_ressources():
    """Returns a list of resources."""
    return Resource.query.all()


def get_resource_from_id(resource_id):
    """Returns a Resource object given it's id.

    Args:
        resource_id: the index of the resource in the database.

    Returns:
        A Resource object.
    """
    resource = Resource.query.filter_by(id=resource_id).first()

    if resource is None:
        logger.warning("Resource not found. Id : {}".format(resource_id))
        raise ResourceNotFound(message="Resource not found",
                               payload={'resource_id': resource_id})
    return resource


def get_resource_from_name(resource_name):
    """Returns a Resource object given it's name.

    Args:
        resource_name: the name of the resource.

    Returns:
        A Resource object.
    """
    resource = Resource.query.filter_by(name=resource_name).first()

    if resource is None:
        logger.warning("Resource not found. Name : {}".format(resource_name))
        raise ResourceNotFound(message="Resource not found",
                               payload={'resource_name': resource_name})
    return resource


def get_resources_from_tags(resource_tags):
    """Returns a Resource object list given their tags.

    Args:
        resource_tags: the tags of the resource we are looking for.

    Returns:
        A Resource object.
    """
    all_resources = get_all_ressources()
    resources = list()

    # Filter the ones matching the tags, TODO: Use database more efficiently
    for resource in all_resources:
        if not resource.tags:
            continue
        if set(resource.tags.split()).intersection(set(resource_tags)) == set(resource_tags):
            resources.append(resource)

    if not resources:
        logger.warning("Resources not found. Tag(s) : {}".format(resource_tags))
        raise ResourceNotFound(message="No resource found matching the tag(s)",
                               payload={'tags': resource_tags})
    return resources


def get_an_available_resource(rid=None, name=None, tags=None):
    """Returns an available resource object.

    Args:
        rid (int): The id
        name (str):
        tags (list):

    Returns:
        (Resource) A resource object
    """
    if rid:
        resource = get_resource_from_id(rid)
    elif name:
        resource = get_resource_from_name(name)
    elif tags:
        resources = get_resources_from_tags(tags)
        for resource in resources:
            if resource.lock_token is None:
                break
    else:
        raise ResourceException(message="Bad Request")

    if resource.lock_token is not None:
        logger.warning("Resource already locked. Id : {}".format(resource.id))
        raise ResourceAlreadyLocked(message="Cannot lock the requested resource, resource(s) already locked",
                                    payload={'id': rid,
                                             'name': name,
                                             'tags': tags
                                             })
    return resource


def lock_resource(rid=None, name=None, tags=None):
    """Lock resource. Raise an exception if the resource is already locked.

    Args:
        rid (int): The id of the resource to lock.
        name (str): The name of the resource to lock.
        tags (list): The tags of the resource to lock.

    Returns:
        The lock token value
    """
    # Prevent concurrent database access in a multi threaded execution context
    with thread_safe_lock:

        resource = get_an_available_resource(rid=rid, name=name, tags=tags)

        resource.lock_token = str(uuid4())
        resource.lock_details = u'Resource locked'
        db.session.commit()

        logger.info("Resource locked. Id : {}".format(resource.id))

        return resource.lock_token, resource


def unlock_resource(resource_id, lock_token):
    """Unlock resource. Raise an exception if the token is invalid or if the resource is already unlocked.

    Args:
        resource_id (int): The id of the resource to unlock.
        lock_token (str): The lock token to authorize the unlock.

    Returns:
        None
    """
    resource = get_resource_from_id(resource_id)

    if resource.lock_token is None:
        logger.warning("Resource already unlocked. Id : {}".format(resource_id))
        raise ResourceAlreadyUnlocked(message="Resource is already unlocked",
                                      payload={'resource_id': resource_id})
    if lock_token != resource.lock_token:
        msg = "Incorrect lock token. Id : {}, lock-token : {}, resource lock-token : {}".format(resource_id,
                                                                                                lock_token,
                                                                                                resource.lock_token)
        logger.warning(msg)
        raise InvalidLockToken(message="Cannot unlock resource, the lock token is not valid.",
                               payload={'resource': resource.dict,
                                        'invalid-lock-token': lock_token})
    resource.lock_token = None
    resource.lock_details = u'Resource available'
    db.session.commit()

    logger.info("Resource unlocked. Id : {}".format(resource_id))


def populate_database_from_file(resource_descriptor):
    """ Populate the database using the resources described in a yaml file.

    Args:
      resource_descriptor (str): the resource descriptor.

    Returns:
        (list) resources name added

    """
    logger.info("Populating the database. Descriptor : {}".format(resource_descriptor))

    with open(resource_descriptor, "r") as f:
        resources = yaml.load(f)

    if resources is None:
        raise ResourceDescriptorIsEmpty(resource_descriptor)

    db.drop_all()
    db.create_all()

    for resource_name in list(resources):

        logger.debug("Add resource : {}".format(resource_name))

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

    return list(resources)
