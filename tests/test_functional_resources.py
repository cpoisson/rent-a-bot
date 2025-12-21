# -*- coding: utf-8 -*-
"""
Resources Functional Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains Rent-A-Bot Resources functional requirements.

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
import rentabot
from rentabot.models import Resource, db

import os
import json

from fixtures import app
from db_utils import reset_database, create_resources, create_resources_with_tags


class TestGetResources(object):
    """
    Title: Retrieve the existing resources.

    As: An automation developer.
    I want: to retrieve the resources.
    So that: I can access to the resource status and information for other purposes.
    """

    def test_get_resources_no_criteria(self, app):
        """
        Title: Retrieve a list of resources without criteria.

        Given: Multiple resources exists.
        And: No criteria is provided.
        When: Requesting the resources information.
        Then: All the available resources are returned.
        """

        # Reset Database
        reset_database()

        # Add resources to the database
        res_count_expected = 10
        create_resources(res_count_expected)

        # Request the available resources
        response = app.get('/rentabot/api/v1.0/resources')

        # Should be a 200 OK
        if response.status_code != 200:
            msg = "Oopsie, status code 200 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

        # Should contains the count of resources expected
        resources = json.loads(response.get_data().decode('utf-8'))['resources']

        res_count_returned = len(list(resources))
        if res_count_returned != res_count_expected:
            msg = "Oopsie, {} resources were expected, received {}.".format(res_count_expected,
                                                                            res_count_returned)
            pytest.fail(msg)

    def test_get_resources_no_criteria_no_resource(self, app):
        """
        Title: Retrieve a list of resources without criteria.

        Given: No resource exists.
        And: No criteria is provided.
        When: Requesting the resources information.
        Then: An empty list is returned.
        """
        # Reset Database
        reset_database()

        # Request the available resources
        response = app.get('/rentabot/api/v1.0/resources')

        # Should be a 200 OK
        if response.status_code != 200:
            msg = "Oopsie, status code 200 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

        res_count_expected = 0
        # Should contains 0 resources
        resources = json.loads(response.get_data().decode('utf-8'))['resources']

        res_count_returned = len(list(resources))
        if res_count_returned != res_count_expected:
            msg = "Oopsie, {} resources were expected, received {}.".format(res_count_expected,
                                                                            res_count_returned)
            pytest.fail(msg)

    def test_get_a_resource(self, app):
        """
        Title: Retrieve an existing resource.

        Given: Multiple resources exists.
        And: No criteria is provided.
        When: Requesting a resource that does exist.
        Then: The corresponding resource
        """

        # Reset Database
        reset_database()

        # Add resources to the database
        create_resources(10)

        # Request an existing resource
        response = app.get('/rentabot/api/v1.0/resources/5')

        # Should be a 200 OK
        if response.status_code != 200:
            msg = "Oopsie, status code 200 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

        # Should contains 0 resources
        resource = json.loads(response.get_data().decode('utf-8'))['resource']

    def test_get_a_resource_does_not_exist(self, app):
        """
        Title: Retrieve a resource that does not exist.

        Given: Multiple resources exists.
        And: No criteria is provided.
        When: Requesting a resource that does exist.
        Then: A 404 error status code is returned.
        """

        # Reset Database
        reset_database()

        # Add resources to the database
        create_resources(10)

        # Request a obviously unkown resource
        response = app.get('/rentabot/api/v1.0/resources/1000')

        # Should be a 404 Not Found
        if response.status_code != 404:
            msg = "Oopsie, status code 404 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)
        # Check that the 404 returned is the app 404 and not a generic one.
        response_json = json.loads(response.get_data().decode('utf-8'))
        assert response_json['resource_id'] == 1000


class TestLockUnlockResourceById(object):
    """
    Title: Lock/Unlock a resource by Id.

    As: An automation developer.
    I want: To lock and unlock a given resource knowing it's Id.
    So that: I can acquire this resource for an exclusive use.
    """

    def test_lock_resource(self, app):
        """
        Title: Lock a resource.

        Given: A resource exists.
        And: The resource is not locked.
        When: Requesting a lock on this resource.
        Then: The resource is locked.
        """
        # Reset Database
        reset_database()

        # Add a resource to the database
        from rentabot import app as flask_app
        with flask_app.app_context():
            db.session.add(Resource(name="resource",
                                    description="I'm a resource!"))
            db.session.commit()

        # Lock the first resource
        response = app.post('/rentabot/api/v1.0/resources/1/lock')

        # Should be a 200 OK
        if response.status_code != 200:
            msg = "Oopsie, status code 200 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

        # Response should contain a lock token
        response_dict = json.loads(response.get_data().decode('utf-8'))
        try:
            lock_token = response_dict['lock-token']
        except KeyError:
            msg = "Oopsie, cannot find the lock-token."
            pytest.fail(msg)
        else:
            if len(lock_token) == 0:
                msg = "Oopsie, the lock token is empty"
                pytest.fail(msg)

        # Resource should be locked with this token
        response = app.get('/rentabot/api/v1.0/resources/1')

        resource = json.loads(response.get_data().decode('utf-8'))['resource']

        if resource['lock-token'] != lock_token:
            msg = "Oopsie, the resource is not locked with the expected lock token."
            pytest.fail(msg)

        return lock_token

    def test_unlock_resource(self, app):
        """
        Title: Unlock a resource.

        Given: A resource exists.
        And: The resource is locked.
        When: Requesting to unlock this resource.
        Then: The resource is unlocked.
        """

        # Lock a resource (use lock test)
        lock_token = self.test_lock_resource(app)

        # Unlock the first resource
        response = app.post('/rentabot/api/v1.0/resources/1/unlock?lock-token={}'.format(lock_token))

        # Should be a 200 OK
        if response.status_code != 200:
            msg = "Oopsie, status code 200 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

        # Resource should be unlocked
        response = app.get('/rentabot/api/v1.0/resources/1')

        resource = json.loads(response.get_data().decode('utf-8'))['resource']

        if resource['lock-token'] is not None:
            msg = "Oopsie, the resource seems to be locked."
            pytest.fail(msg)

    def test_unlock_resource_bad_token(self, app):
        """
        Title: Unlock a resource.

        Given: A resource exists.
        And: The resource is locked.
        When: Requesting to unlock this resource.
        Then: The resource is unlocked.
        """

        # Lock a resource (use lock test)
        self.test_lock_resource(app)

        # Create a bad lock token
        lock_token = 'verybadlocktokenbadbadbad'

        # Unlock the first resource
        response = app.post('/rentabot/api/v1.0/resources/1/unlock?lock-token={}'.format(lock_token))

        # Should be a 403 Forbidden
        if response.status_code != 403:
            msg = "Oopsie, status code 403 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

        # Resource should be still locked
        response = app.get('/rentabot/api/v1.0/resources/1')

        resource = json.loads(response.get_data().decode('utf-8'))['resource']

        if resource['lock-token'] is None:
            msg = "Oopsie, the resource seems to be unlocked."
            pytest.fail(msg)

    def test_lock_resource_already_locked(self, app):
        """
        Title: Lock a resource.

        Given: A resource exists.
        And: The resource is already locked.
        When: Requesting a lock on this resource.
        Then: The server answer with an error code and stating that the resource is already locked.
        """
        # Lock a resource (use lock test)
        self.test_lock_resource(app)

        # Lock the resource again
        response = app.post('/rentabot/api/v1.0/resources/1/lock')

        # Should be a 403 Forbidden
        if response.status_code != 403:
            msg = "Oopsie, status code 403 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

    def test_unlock_resource_already_unlocked(self, app):
        """
        Title: Unlock a resource.

        Given: A resource exists.
        And: The resource is unlocked.
        When: Requesting to unlock this resource.
        Then: The server answer with an error code and stating that the resource is already unlocked.
        """

        # Reset Database
        reset_database()

        # Add a resource to the database
        from rentabot import app as flask_app
        with flask_app.app_context():
            db.session.add(Resource(name="resource",
                                    description="I'm a resource!"))
            db.session.commit()

        # Unlock the first resource
        response = app.post('/rentabot/api/v1.0/resources/1/unlock')

        # Should be a 403 Forbidden
        if response.status_code != 403:
            msg = "Oopsie, status code 403 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

    @pytest.mark.parametrize('cmd', ['lock', 'unlock'])
    def test_unlock_unlock_resource_does_not_exist(self, app, cmd):
        """
        Title: Unlock or Lock a resource that does not exist.

        Given: A resource does not exists.
        When: Requesting to unlock or lock this resource.
        Then: A 404 status code is returned.
        """

        # Reset Database
        reset_database()

        # Add a resource to the database
        from rentabot import app as flask_app
        with flask_app.app_context():
            db.session.add(Resource(name="resource",
                                    description="I'm a resource!"))
            db.session.commit()

        # Unlock an arbitrary resource 1000000, far away
        resource_id = 100000
        response = app.post('/rentabot/api/v1.0/resources/{}/{}'.format(resource_id, cmd))

        # Response should be a 404 Not Found
        if response.status_code != 404:
            msg = "Oopsie, status code 404 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

        # Check that the 404 returned is the app 404 and not a generic one.
        response_json = json.loads(response.get_data().decode('utf-8'))
        assert response_json['resource_id'] == resource_id


class TestLockResourceByCriteria(object):
    """
    Title: Log a resource by criteria (resource Id, name or tags)

    As: An automation developer
    I want: To lock a resource using a name or tags.
    So that: I can directly lock the resource I'm interested in, without having to check if the resource is available.
    """

    def test_lock_resource_by_tags(self, app):
        """
        Title: Lock a resource by matching tags

        Given: A resource exists with known tags
        And: The resource is not locked.
        When: Requesting a lock on this resource using it's tags.
        Then: The resource is locked.
        """
        # Reset Database
        reset_database()

        # Add some resources
        create_resources_with_tags()

        # Lock an arduino with leds
        tag_1 = "arduino"
        tag_2 = "leds"
        response = app.post('/rentabot/api/v1.0/resources/lock?tag={}&tag={}'.format(tag_1, tag_2))

        # Should be a 200 OK
        if response.status_code != 200:
            msg = "Oopsie, status code 200 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

        response_dict = json.loads(response.get_data().decode('utf-8'))

        # Response should contain a lock token
        try:
            lock_token = response_dict['lock-token']
        except KeyError:
            msg = "Oopsie, cannot find the lock-token."
            pytest.fail(msg)
        else:
            if len(lock_token) == 0:
                msg = "Oopsie, the lock token is empty"
                pytest.fail(msg)

        # Resource tags should match with arduino and leds tags
        resource_tags = response_dict['resource']['tags'].split()

        if tag_1 not in resource_tags:
            pytest.fail("{} not in resource tags {}".format(tag_1, resource_tags))
        if tag_2 not in resource_tags:
            pytest.fail("{} not in resource tags {}".format(tag_1, resource_tags))

        # Retry to lock the same tags (only one is available here)

        response = app.post('/rentabot/api/v1.0/resources/lock?tag={}&tag={}'.format(tag_1, tag_2))

        # Should be a 403 Forbidden
        if response.status_code != 403:
            msg = "Oopsie, status code 403 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

    def test_lock_resource_by_tag_not_exists(self, app):
        """
        Title: Lock a resource using not existing tags

        Given: A tag does not exist
        When: Requesting a lock on  using this tag
        Then: A 404 Not found is returned
        """
        # Reset Database
        reset_database()

        # Add some resources
        create_resources_with_tags()

        # Lock an arduino with leds
        tag_1 = "arduino"
        tag_2 = "acapulco"
        response = app.post('/rentabot/api/v1.0/resources/lock?tag={}&tag={}'.format(tag_1, tag_2))

        # Should be a 404
        if response.status_code != 404:
            msg = "Oopsie, status code 404 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

    def test_lock_resource_by_name(self, app):
        """
        Title: Lock a resource by matching name

        Given: A resource exists with a known name
        And: The resource is not locked.
        When: Requesting a lock on this resource using its name.
        Then: The resource is locked.
        """
        # Reset Database
        reset_database()

        # Add some resources
        create_resources_with_tags()

        # Lock an arduino with leds
        resource_name = "arduino-1"
        response = app.post('/rentabot/api/v1.0/resources/lock?name={}'.format(resource_name))

        # Should be a 200 OK
        if response.status_code != 200:
            msg = "Oopsie, status code 200 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

        response_dict = json.loads(response.get_data().decode('utf-8'))

        # Response should contain a lock token
        try:
            lock_token = response_dict['lock-token']
        except KeyError:
            msg = "Oopsie, cannot find the lock-token."
            pytest.fail(msg)
        else:
            if len(lock_token) == 0:
                msg = "Oopsie, the lock token is empty"
                pytest.fail(msg)

        # Resource name should match with the name provided
        returned_name = response_dict['resource']['name']

        if returned_name != resource_name:
            pytest.fail("{} is not the awaited resource name {}.".format(returned_name, resource_name))

        # Retry to lock the same name (only one is available here)

        response = app.post('/rentabot/api/v1.0/resources/lock?name={}'.format(resource_name))

        # Should be a 403 Forbidden
        if response.status_code != 403:
            msg = "Oopsie, status code 403 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

    def test_lock_resource_by_name_not_exists(self, app):
        """
        Title: Lock a resource using a resource with a non existing name

        Given: A resource name does not exist
        When: Requesting a lock on this resource using this name
        Then: A 404 Not found is returned
        """
        # Reset Database
        reset_database()

        # Add some resources
        create_resources_with_tags()

        # Lock using a bad name
        response = app.post('/rentabot/api/v1.0/resources/lock?name=i-do-not-exist')

        # Should be a 404
        if response.status_code != 404:
            msg = "Oopsie, status code 404 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

    def test_lock_resource_by_unsupported_criteria_type(self, app):
        """
        Title: Lock a resource using a not supported criteria

        Given: A resource name does not exist
        When: Requesting a lock using this criteria type
        Then: A 400 bad requests must be returned
        """
        # Reset Database
        reset_database()

        # Add some resources
        create_resources_with_tags()

        # Lock using a not supported criteria
        response = app.post('/rentabot/api/v1.0/resources/lock?color=blue')

        # Should be a 400
        if response.status_code != 400:
            msg = "Oopsie, status code 404 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)
