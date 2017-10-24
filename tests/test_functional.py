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
import rentabot
from rentabot.models import Resource, db

import os
import json, yaml

@pytest.fixture
def app(tmpdir):
    rentabot.app.testing = True
    # Use pytest tmpdir for a temp database path
    rentabot.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(tmpdir.strpath, 'rent-a-bot.sqlite')
    return rentabot.app.test_client()


def reset_database():
    """Drop and create tables."""
    # Reset database
    db.drop_all()

    # Create tables
    db.create_all()


def create_resources(qty):
    """ Create resources in the database.

    Args:
        qty: quantity of resources to create

    """
    for x in range(qty):
        db.session.add(Resource(name="resource_{}".format(x),
                                description="I'm the resource {}!".format(x)))
    db.session.commit()


class TestInitResourcesFromDescriptor(object):
    """
    Title: Init the database with a YAML configuration file at startup

    As: An application user
    I want: The application to automatically populate the database with resources at startup
    So that: The application run from scratch with static resources available.
    """

    def test_init_db_with_configuration_file(self, app):
        """
        Title:

        Given: A yaml configuration file with resources described exists
        And: An environment variable exists to indicate the path of the resource descriptor
        And: Rent a bot is not yet started
        When: Starting rent a bot
        Then: The database is created with the resources described in the configuration file
        """

        try:
            descriptor_path = os.path.abspath(os.environ['RENTABOT_RESOURCE_DESCRIPTOR'])
        except KeyError:
            pytest.skip("No ressource descriptor provided, skipping test.")

        with open(descriptor_path, 'r') as f:
            input_resources = yaml.load(f)

        # Request the available resources
        response = app.get('/rentabot/api/v1.0/resources')

        # Should be a 200 OK
        if response.status_code != 200:
            msg = "Oopsie, status code 200 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

        # Should contains the count of resources expected
        resources = json.loads(response.get_data().decode('utf-8'))['resources']

        res_count_expected = len(list(input_resources))
        res_count_returned = len(list(resources))
        if res_count_returned != res_count_expected:
            msg = "Oopsie, {} resources were expected, received {}.".format(res_count_expected,
                                                                            res_count_returned)
            pytest.fail(msg)


class TestGetResources(object):
    """
    Title: Retrieve the existing resources by criteria.

    As: An automation application.
    I want: An API to retrieve the resources by criteria.
    So that: I can access to a list of resources by criteria.
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


class TestLockUnlockResource(object):
    """
    Title: Lock/Unlock a resource.

    As: An automation application.
    I want: An API to lock and unlock a given resource.
    So that: I can state to 3rd parties that this given resource is locked.
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
        db.session.add(Resource(name="resource",
                                description="I'm a resource!"))
        db.session.commit()

        # Unlock an arbitrary resource 1000000, far away
        response = app.post('/rentabot/api/v1.0/resources/1000000/{}'.format(cmd))

        # Response should be a 404 Not Found
        if response.status_code != 404:
            msg = "Oopsie, status code 404 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)


