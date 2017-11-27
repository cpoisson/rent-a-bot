# -*- coding: utf-8 -*-
"""
Resource Descriptor Functional Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains Rent-A-Bot resource descriptor unit tests.
"""

import os
import pytest
from rentabot.controllers import populate_database_from_file
from rentabot.exceptions import ResourceDescriptorIsEmpty

RESOURCE_DESCRIPTOR_EMPTY = "# I'm so empty...\n"

RESOURCE_DESCRIPTOR_DUPLICATED = """
# Oopsie, coffee-machine is duplicated

coffee-machine:
    description: "Kitchen coffee machine"
    endpoint: "tcp://192.168.1.50"
    tags: "coffee kitchen food"

coffee-machine:
    description: "Kitchen coffee machine"
    endpoint: "tcp://192.168.1.50"
    tags: "coffee kitchen food"
"""


def test_init_db_with_an_empty_file_descriptor(tmpdir):
    """
    Title: Empty descriptor entry MUST except

    Given: A yaml configuration file with duplicated resources (same name)
    And: Rent a bot is not yet started
    When: Starting rent a bot
    Then: A ResourceDescriptorDuplicatedName exception MUST be raised
    """
    file_descriptor_path = os.path.join("/tmp", "tmp_descriptor.yml")
    with open(file_descriptor_path, "w") as f:
        f.write(RESOURCE_DESCRIPTOR_EMPTY)
    try:
        populate_database_from_file(file_descriptor_path)
    except ResourceDescriptorIsEmpty:
        pass  # It's the expected Exception


def test_init_db_with_duplicated_resource_entry():
    """
    Title: Duplicated resource entry MUST except

    Given: A yaml configuration file with duplicated resources (same name)
    And: Rent a bot is not yet started
    When: Starting rent a bot
    Then: The last name entry is taken into account
    """
    file_descriptor_path = os.path.join("/tmp", "tmp_descriptor.yml")

    with open(file_descriptor_path, "w") as f:
        f.write(RESOURCE_DESCRIPTOR_DUPLICATED)

    if len(populate_database_from_file(file_descriptor_path)) != 1:
        pytest.fail("Expected only one resource")
