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

    def __str__(self):
        """Return string representation of the exception."""
        return self.message or ""

    def to_dict(self):
        """Serialize exception to dictionary."""
        rv = dict(self.payload or ())
        rv["message"] = self.message
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
    """Raised when the lock token is not valid."""

    status_code = 403  # Forbidden

    def __init__(self, *argv, **kwargs):
        ResourceException.__init__(self, *argv, **kwargs)


class InvalidTTL(ResourceException):
    """Raised when TTL validation fails."""

    status_code = 400  # Bad Request

    def __init__(self, *argv, **kwargs):
        ResourceException.__init__(self, *argv, **kwargs)


# - [ Reservation Exception ] ------------------------------------------------


class ReservationException(Exception):
    """Base Reservation Exception."""

    status_code = 400  # Bad Request

    def __init__(self, message=None, payload=None):
        Exception.__init__(self)
        self.message = message
        self.payload = payload

    def __str__(self):
        """Return string representation of the exception."""
        return self.message or ""

    def to_dict(self):
        """Serialize exception to dictionary."""
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


class ReservationNotFound(ReservationException):
    """Raised when a reservation is not found."""

    status_code = 404  # Not Found

    def __init__(self, *argv, **kwargs):
        ReservationException.__init__(self, *argv, **kwargs)


class ReservationNotFulfilled(ReservationException):
    """Raised when trying to claim a reservation that isn't fulfilled yet."""

    status_code = 409  # Conflict

    def __init__(self, *argv, **kwargs):
        ReservationException.__init__(self, *argv, **kwargs)


class ReservationClaimExpired(ReservationException):
    """Raised when claim window has expired."""

    status_code = 410  # Gone

    def __init__(self, *argv, **kwargs):
        ReservationException.__init__(self, *argv, **kwargs)


class InsufficientResources(ReservationException):
    """Raised when not enough resources are available."""

    status_code = 409  # Conflict

    def __init__(self, *argv, **kwargs):
        ReservationException.__init__(self, *argv, **kwargs)


class ReservationCannotBeCancelled(ReservationException):
    """Raised when trying to cancel a fulfilled/claimed reservation."""

    status_code = 409  # Conflict

    def __init__(self, *argv, **kwargs):
        ReservationException.__init__(self, *argv, **kwargs)


class InvalidReservationTags(ReservationException):
    """Raised when reservation tags validation fails."""

    status_code = 400  # Bad Request

    def __init__(self, *argv, **kwargs):
        ReservationException.__init__(self, *argv, **kwargs)


# - [ Resource Descriptor Exception ] ----------------------------------------


class ResourceDescriptorException(Exception):
    """Base resource descriptor exception"""

    def __init__(self, file_descriptor, message=None):
        if message is None:
            self.message = f"An error occurred with resource descriptor: {file_descriptor}"
        else:
            self.message = message
        self.file_descriptor = file_descriptor


class ResourceDescriptorIsEmpty(ResourceDescriptorException):
    """The resource descriptor does not contain any resources"""

    def __init__(self, file_descriptor):
        msg = f"The resource descriptor is empty : {file_descriptor}"
        ResourceDescriptorException.__init__(self, file_descriptor, message=msg)
