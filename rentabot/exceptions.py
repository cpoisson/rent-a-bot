# -*- coding: utf-8 -*-
"""
rentabot.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains rent-a-bot custom exceptions.
"""


# - [ Resource Exception ] ---------------------------------------------------

class ResourceException(Exception):
    """Base Resource Exception."""

    status_code = 400  # Bad Request

    def __init__(self, message=None, payload=None):
        Exception.__init__(self)
        self.message = message
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


class ResourceAlreadyUnlocked(ResourceException):
    """Raised when a resource is already available."""

    status_code = 403  # Forbidden

    def __init__(self, *argv, **kwargs):
        ResourceException.__init__(self, *argv, **kwargs)


class ResourceAlreadyLocked(ResourceException):
    """Raised when a resource is not available."""

    status_code = 403  # Forbidden

    def __init__(self, *argv, **kwargs):
        ResourceException.__init__(self, *argv, **kwargs)


class InvalidLockToken(ResourceException):
    """Raised a the lock token is not valid."""

    status_code = 403  # Forbidden

    def __init__(self, *argv, **kwargs):
        ResourceException.__init__(self, *argv, **kwargs)


# - [ Resource Descriptor Exception ] ----------------------------------------

class ResourceDescriptorException(Exception):
    """Base resource descriptor exception"""
    def __init__(self, file_descriptor, message=None):
        if message is None:
            self.message = "An error occurred with resource descriptor: {}".format(file_descriptor)
        else:
            self.message = message
        self.file_descriptor = file_descriptor


class ResourceDescriptorIsEmpty(ResourceDescriptorException):
    """The resource descriptor does not contain any resources"""
    def __init__(self, file_descriptor):
        msg = "The resource descriptor is empty : {}".format(file_descriptor)
        ResourceDescriptorException.__init__(self, file_descriptor, message=msg)
