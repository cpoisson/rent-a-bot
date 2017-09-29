# -*- coding: utf-8 -*-
"""
rentabot.controllers
~~~~~~~~~~~~~~~~~~~~

This module contains rent-a-bot functions related to database manipulation.
"""


from rentabot.models import Resource, db
from rentabot.exceptions import ResourceNotAvailable, InvalidLockKey
from uuid import uuid4


def lock_resource(resource):
    """Lock resource.

    Args:
        resource: Resource object.

    Returns:

    """
    if resource.status == Resource.STATUS[u'locked']:
        raise ResourceNotAvailable
    else:
        resource.lock_key = str(uuid4())
        resource.status = Resource.STATUS[u'locked']
        resource.status_details = u'Resource locked.'
        db.session.commit()
    return resource.lock_key


def unlock_resource(resource, lock_key):
    """Lock resource.

    Args:
        resource: Resource object.

    Returns:

    """
    if lock_key != resource.lock_key:
        raise InvalidLockKey(lock_key)

    if resource.status == Resource.STATUS[u'locked']:
        resource.lock_key = u''
        resource.status = Resource.STATUS[u'available']
        resource.status_details = u'Resource available.'
        db.session.commit()
