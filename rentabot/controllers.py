# -*- coding: utf-8 -*-
"""
rentabot.controllers
~~~~~~~~~~~~~~~~~~~~

This module contains rent-a-bot functions related to database manipulation.
"""


from rentabot.models import Resource, db
from rentabot.exceptions import ResourceAlreadyLocked, ResourceAlreadyUnlocked, InvalidLockToken
from uuid import uuid4


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

