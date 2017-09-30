# -*- coding: utf-8 -*-
"""
rentabot.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains rent-a-bot custom exceptions.
"""


class ResourceException(Exception):
    """Base Resource Exception."""

    status_code = 400  # Bad Request

    def __init__(self, message=None, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    @property
    def dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class ResourceNotFound(ResourceException):
    """Raised when a resource is not available."""

    status_code = 404  # Not Found

    def __init__(self, *argv, **kwargs):
        ResourceException.__init__(self, *argv, **kwargs)


class ResourceAlreadyLocked(ResourceException):
    """Raised when a resource is not available."""

    status_code = 423  # Locked

    def __init__(self, *argv, **kwargs):
        ResourceException.__init__(self, *argv, **kwargs)


class InvalidLockToken(ResourceException):
    """Raised a the lock token is not valid."""

    status_code = 403  # Forbidden

    def __init__(self, *argv, **kwargs):
        ResourceException.__init__(self, *argv, **kwargs)
