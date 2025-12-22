# -*- coding: utf-8 -*-
"""
Resource Descriptor Functional Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains Rent-A-Bot resource descriptor functional requirements.

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
import yaml
import json
import os

from fixtures import app


class TestInitResourcesFromDescriptor(object):
    """
    Title: Init the database with a YAML configuration file at startup

    As: An application user
    I want: The application to automatically populate the database with resources at startup
    So that: The application run from scratch with static resources available.
    """

    def test_init_db_with_configuration_file(self, app):
        """
        Title: Init DB with a resource descriptor file

        Given: A yaml configuration file with resources described exists
        And: An environment variable exists to indicate the path of the resource descriptor
        And: Rent a bot is not yet started
        When: Starting rent a bot
        Then: The database is created with the resources described in the configuration file
        """
        # Use the resource descriptor from test assets
        test_dir = os.path.dirname(os.path.abspath(__file__))
        descriptor_path = os.path.join(test_dir, "assets", "resource_descriptor.yaml")

        # Populate the database from the descriptor file
        from rentabot.controllers import populate_database_from_file

        populate_database_from_file(descriptor_path)

        with open(descriptor_path, "r") as f:
            input_resources = yaml.load(f, Loader=yaml.SafeLoader)

        # Request the available resources
        response = app.get("/rentabot/api/v1.0/resources")

        # Should be a 200 OK
        if response.status_code != 200:
            msg = "Oopsie, status code 200 was awaited, received {}.".format(response.status_code)
            pytest.fail(msg)

        # Should contains the count of resources expected
        resources = response.json()["resources"]

        res_count_expected = len(list(input_resources))
        res_count_returned = len(list(resources))
        if res_count_returned != res_count_expected:
            msg = "Oopsie, {} resources were expected, received {}.".format(
                res_count_expected, res_count_returned
            )
            pytest.fail(msg)
