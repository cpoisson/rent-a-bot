# -*- coding: utf-8 -*-
"""
Functional Requirements
~~~~~~~~~~~~~~~~~~~~~~~

This module contains Rent-A-Bot functional requirements.

Tests are organized as followed:

class TestUserStory(object):
    (UserStory description in the docstring)

    def test_acceptance_criteria_1():
        (Acceptance Criteria description in the docstring)
        some test...

    def test_acceptance_criteria_2():
        (Acceptance Criteria description in the docstring)
        some test...

"""
import pytest


class TestGetResources(object):
    """
    Title: Retrieve the existing resources by criteria.

    As: An automation application.
    I want: An API to retrieve the resources by criteria.
    So that: I can access to a list of resources by criteria.
    """

    @pytest.mark.skip
    def test_get_resources_no_criteria(self):
        """
        Title: Retrieve a list of resources without criteria.

        Given: Multiple resources exists.
        And: No criteria is provided.
        When: Requesting the resources information.
        Then: All the available resources are returned.
        """

        pass

    @pytest.mark.skip
    def test_acceptance_criteria(self):
        """
        Title:

        Given:
        And:
        When:
        Then:
        """
        pass


class TestLockUnlockResource(object):
    """
    Title: Lock/Unlock a resource.

    As: An automation application.
    I want: An API to retrieve to lock and unlock a given resource.
    So that: I can state to 3rd parties that this given resource is locked.
    """

    @pytest.mark.skip
    def test_lock_resource(self):
        """
        Title: Lock a resource.

        Given: A resource exists.
        And: The resource is not locked.
        When: Requesting a lock on this resource.
        Then: The resource is locked.
        """
        pass

    @pytest.mark.skip
    def test_unlock_resource(self):
        """
        Title: Unlock a resource.

        Given: A resource exists.
        And: The resource is locked.
        When: Requesting to unlock this resource.
        Then: The resource is unlocked.
        """
        pass

    @pytest.mark.skip
    def test_lock_resource_already_locked(self):
        """
        Title: Lock a resource.

        Given: A resource exists.
        And: The resource is already locked.
        When: Requesting a lock on this resource.
        Then: The server answer with an error code and stating that the resource is already locked.
        """
        pass

    @pytest.mark.skip
    def test_unlock_resource_already_unlocked(self):
        """
        Title: Unlock a resource.

        Given: A resource exists.
        And: The resource is unlocked.
        When: Requesting to unlock this resource.
        Then: The server answer with an error code and stating that the resource is already unlocked.
        """
        pass

