# -*- coding: utf-8 -*-
"""
rentabot.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains rent-a-bot custom exceptions.
"""


class ResourceNotAvailable(Exception):
    """Raised when a resource is not available."""


class InvalidLockKey(ValueError):
    """Raised when the lock key is not valid"""

