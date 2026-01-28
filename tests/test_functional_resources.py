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
from db_utils import create_resources, create_resources_with_tags, reset_database

from rentabot.models import Resource


class TestGetResources:
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
        response = app.get("/api/v1/resources")

        # Should be a 200 OK
        if response.status_code != 200:
            msg = f"Oopsie, status code 200 was awaited, received {response.status_code}."
            pytest.fail(msg)

        # Should contains the count of resources expected
        resources = response.json()["resources"]

        res_count_returned = len(list(resources))
        if res_count_returned != res_count_expected:
            msg = f"Oopsie, {res_count_expected} resources were expected, received {res_count_returned}."
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
        response = app.get("/api/v1/resources")

        # Should be a 200 OK
        if response.status_code != 200:
            msg = f"Oopsie, status code 200 was awaited, received {response.status_code}."
            pytest.fail(msg)

        res_count_expected = 0
        # Should contains 0 resources
        resources = response.json()["resources"]

        res_count_returned = len(list(resources))
        if res_count_returned != res_count_expected:
            msg = f"Oopsie, {res_count_expected} resources were expected, received {res_count_returned}."
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
        response = app.get("/api/v1/resources/5")

        # Should be a 200 OK
        if response.status_code != 200:
            msg = f"Oopsie, status code 200 was awaited, received {response.status_code}."
            pytest.fail(msg)

        # Should contains 0 resources
        response.json()["resource"]

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
        response = app.get("/api/v1/resources/1000")

        # Should be a 404 Not Found
        if response.status_code != 404:
            msg = f"Oopsie, status code 404 was awaited, received {response.status_code}."
            pytest.fail(msg)
        # Check that the 404 returned is the app 404 and not a generic one.
        response_json = response.json()
        assert response_json["resource_id"] == 1000


class TestLockUnlockResourceById:
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

        # Add a resource to memory
        import rentabot.models
        from rentabot.models import resources_by_id

        resource = Resource(id=1, name="resource", description="I'm a resource!")
        resources_by_id[1] = resource
        rentabot.models.next_resource_id = 2

        # Lock the first resource
        response = app.post("/api/v1/resources/1/lock")

        # Should be a 200 OK
        if response.status_code != 200:
            msg = f"Oopsie, status code 200 was awaited, received {response.status_code}."
            pytest.fail(msg)

        # Response should contain a lock token
        response_dict = response.json()
        try:
            lock_token = response_dict["lock-token"]
        except KeyError:
            msg = "Oopsie, cannot find the lock-token."
            pytest.fail(msg)
        else:
            if len(lock_token) == 0:
                msg = "Oopsie, the lock token is empty"
                pytest.fail(msg)

        # Resource should be locked with this token
        response = app.get("/api/v1/resources/1")

        resource = response.json()["resource"]

        if resource["lock-token"] != lock_token:
            msg = "Oopsie, the resource is not locked with the expected lock token."
            pytest.fail(msg)

    def test_unlock_resource(self, app):
        """
        Title: Unlock a resource.

        Given: A resource exists.
        And: The resource is locked.
        When: Requesting to unlock this resource.
        Then: The resource is unlocked.
        """

        # Reset Database
        reset_database()

        # Add a resource to memory
        import rentabot.models

        resource = Resource(id=1, name="resource", description="I'm a resource!")
        rentabot.models.resources_by_id[1] = resource
        rentabot.models.next_resource_id = 2

        # Lock the first resource
        response = app.post("/api/v1/resources/1/lock")
        lock_token = response.json()["lock-token"]

        # Unlock the first resource
        response = app.post(f"/api/v1/resources/1/unlock?lock-token={lock_token}")

        # Should be a 200 OK
        if response.status_code != 200:
            msg = f"Oopsie, status code 200 was awaited, received {response.status_code}."
            pytest.fail(msg)

        # Resource should be unlocked
        response = app.get("/api/v1/resources/1")

        resource = response.json()["resource"]

        if resource["lock-token"] != "":
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
        lock_token = "verybadlocktokenbadbadbad"

        # Unlock the first resource
        response = app.post(f"/api/v1/resources/1/unlock?lock-token={lock_token}")

        # Should be a 403 Forbidden
        if response.status_code != 403:
            msg = f"Oopsie, status code 403 was awaited, received {response.status_code}."
            pytest.fail(msg)

        # Resource should be still locked
        response = app.get("/api/v1/resources/1")

        resource = response.json()["resource"]

        if resource["lock-token"] == "":
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
        response = app.post("/api/v1/resources/1/lock")

        # Should be a 403 Forbidden
        if response.status_code != 403:
            msg = f"Oopsie, status code 403 was awaited, received {response.status_code}."
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

        # Add a resource to memory
        import rentabot.models
        from rentabot.models import resources_by_id

        resource = Resource(id=1, name="resource", description="I'm a resource!")
        resources_by_id[1] = resource
        rentabot.models.next_resource_id = 2

        # Unlock the first resource
        response = app.post("/api/v1/resources/1/unlock")

        # Should be a 403 Forbidden
        if response.status_code != 403:
            msg = f"Oopsie, status code 403 was awaited, received {response.status_code}."
            pytest.fail(msg)

    @pytest.mark.parametrize("cmd", ["lock", "unlock"])
    def test_unlock_unlock_resource_does_not_exist(self, app, cmd):
        """
        Title: Unlock or Lock a resource that does not exist.

        Given: A resource does not exists.
        When: Requesting to unlock or lock this resource.
        Then: A 404 status code is returned.
        """

        # Reset Database
        reset_database()

        # Add a resource to memory
        import rentabot.models
        from rentabot.models import resources_by_id

        resource = Resource(id=1, name="resource", description="I'm a resource!")
        resources_by_id[1] = resource
        rentabot.models.next_resource_id = 2

        # Unlock an arbitrary resource 1000000, far away
        resource_id = 100000
        response = app.post(f"/api/v1/resources/{resource_id}/{cmd}")

        # Response should be a 404 Not Found
        if response.status_code != 404:
            msg = f"Oopsie, status code 404 was awaited, received {response.status_code}."
            pytest.fail(msg)

        # Check that the 404 returned is the app 404 and not a generic one.
        response_json = response.json()
        assert response_json["resource_id"] == resource_id


class TestLockResourceByCriteria:
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
        response = app.post(f"/api/v1/resources/lock?tag={tag_1}&tag={tag_2}")

        # Should be a 200 OK
        if response.status_code != 200:
            msg = f"Oopsie, status code 200 was awaited, received {response.status_code}."
            pytest.fail(msg)

        response_dict = response.json()

        # Response should contain a lock token
        try:
            lock_token = response_dict["lock-token"]
        except KeyError:
            msg = "Oopsie, cannot find the lock-token."
            pytest.fail(msg)
        else:
            if len(lock_token) == 0:
                msg = "Oopsie, the lock token is empty"
                pytest.fail(msg)

        # Resource tags should match with arduino and leds tags
        resource_tags = [tag.strip() for tag in response_dict["resource"]["tags"].split(",")]

        if tag_1 not in resource_tags:
            pytest.fail(f"{tag_1} not in resource tags {resource_tags}")
        if tag_2 not in resource_tags:
            pytest.fail(f"{tag_1} not in resource tags {resource_tags}")

        # Retry to lock the same tags (only one is available here)

        response = app.post(f"/api/v1/resources/lock?tag={tag_1}&tag={tag_2}")

        # Should be a 403 Forbidden
        if response.status_code != 403:
            msg = f"Oopsie, status code 403 was awaited, received {response.status_code}."
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
        response = app.post(f"/api/v1/resources/lock?tag={tag_1}&tag={tag_2}")

        # Should be a 404
        if response.status_code != 404:
            msg = f"Oopsie, status code 404 was awaited, received {response.status_code}."
            pytest.fail(msg)

    def test_lock_resource_by_tags_all_locked(self, app):
        """
        Title: Lock a resource by tags when all matching resources are already locked

        Given: Multiple resources exist with specific tags
        And: All resources with those tags are already locked
        When: Requesting a lock on a resource using those tags
        Then: A 403 Forbidden is returned
        """
        # Reset Database
        reset_database()

        # Add some resources
        create_resources_with_tags()

        # Lock all resources with 'multipurpose' tag
        tag = "multipurpose"

        # Lock first multipurpose resource
        response1 = app.post(f"/api/v1/resources/lock?tag={tag}")
        if response1.status_code != 200:
            msg = (
                f"First lock failed: status code 200 was awaited, received {response1.status_code}."
            )
            pytest.fail(msg)

        # Lock second multipurpose resource
        response2 = app.post(f"/api/v1/resources/lock?tag={tag}")
        if response2.status_code != 200:
            msg = f"Second lock failed: status code 200 was awaited, received {response2.status_code}."
            pytest.fail(msg)

        # Try to lock another multipurpose resource (all are now locked)
        response3 = app.post(f"/api/v1/resources/lock?tag={tag}")

        # Should be a 403 Forbidden
        if response3.status_code != 403:
            msg = f"Oopsie, status code 403 was awaited, received {response3.status_code}."
            pytest.fail(msg)

    def test_lock_resource_by_tags_with_resource_without_tags(self, app):
        """
        Title: Lock a resource by tags when some resources have no tags

        Given: Multiple resources exist, some with tags and some without
        When: Requesting a lock on a resource using tags
        Then: Only resources with matching tags are considered
        """
        # Reset Database
        reset_database()

        # Add resources with tags
        create_resources_with_tags()

        # Add a resource without tags
        import rentabot.models
        from rentabot.models import Resource, resources_by_id

        resource = Resource(
            id=rentabot.models.next_resource_id,
            name="resource-without-tags",
            description="I have no tags",
            tags="",
        )
        resources_by_id[resource.id] = resource
        rentabot.models.next_resource_id += 1

        # Lock a resource with arduino tag (should not select the one without tags)
        tag = "arduino"
        response = app.post(f"/api/v1/resources/lock?tag={tag}")

        # Should be a 200 OK
        if response.status_code != 200:
            msg = f"Oopsie, status code 200 was awaited, received {response.status_code}."
            pytest.fail(msg)

        # Verify the locked resource has tags
        locked_resource = response.json()["resource"]
        if locked_resource["tags"] is None:
            pytest.fail("Resource without tags should not have been selected")

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
        response = app.post("/api/v1/resources/lock?color=blue")

        # Should be a 400
        if response.status_code != 400:
            msg = f"Oopsie, status code 404 was awaited, received {response.status_code}."
            pytest.fail(msg)


class TestExtendResourceLock:
    """
    Title: Extend a resource lock duration.

    As: An automation developer.
    I want: To extend the duration of an existing lock on a resource.
    So that: I can continue using the resource without losing the lock.
    """

    def test_extend_lock_success(self, app):
        """
        Title: Extend a lock successfully.

        Given: A resource exists.
        And: The resource is locked.
        When: Requesting to extend the lock with valid token and additional TTL.
        Then: The lock is extended and new expiration time is returned.
        """
        # Reset Database
        reset_database()

        # Add a resource to memory
        import rentabot.models
        from rentabot.models import resources_by_id

        resource = Resource(id=1, name="resource", description="I'm a resource!")
        resource = resource.model_copy(update={"max_lock_duration": 7200})
        resources_by_id[1] = resource
        rentabot.models.next_resource_id = 2

        # Lock the resource
        response = app.post("/api/v1/resources/1/lock")
        if response.status_code != 200:
            msg = f"Oopsie, lock failed with status code {response.status_code}."
            pytest.fail(msg)

        lock_token = response.json()["lock-token"]

        # Extend the lock
        additional_ttl = 600
        response = app.post(
            f"/api/v1/resources/1/extend?lock-token={lock_token}&additional-ttl={additional_ttl}"
        )

        # Should be a 200 OK
        if response.status_code != 200:
            msg = f"Oopsie, status code 200 was awaited, received {response.status_code}."
            pytest.fail(msg)

        # Response should contain expected fields
        response_dict = response.json()
        if "message" not in response_dict:
            pytest.fail("Response should contain 'message' field")
        if "new-expires-at" not in response_dict:
            pytest.fail("Response should contain 'new-expires-at' field")
        if "total-lock-duration" not in response_dict:
            pytest.fail("Response should contain 'total-lock-duration' field")

    def test_extend_lock_success_new_api(self, app):
        """
        Title: Extend a lock successfully using new API path.

        Given: A resource exists.
        And: The resource is locked.
        When: Requesting to extend the lock using /api/v1 path.
        Then: The lock is extended and new expiration time is returned.
        """
        # Reset Database
        reset_database()

        # Add a resource to memory
        import rentabot.models
        from rentabot.models import resources_by_id

        resource = Resource(id=1, name="resource", description="I'm a resource!")
        resource = resource.model_copy(update={"max_lock_duration": 7200})
        resources_by_id[1] = resource
        rentabot.models.next_resource_id = 2

        # Lock the resource
        response = app.post("/api/v1/resources/1/lock")
        if response.status_code != 200:
            msg = f"Oopsie, lock failed with status code {response.status_code}."
            pytest.fail(msg)

        lock_token = response.json()["lock-token"]

        # Extend the lock using new API path
        additional_ttl = 600
        response = app.post(
            f"/api/v1/resources/1/extend?lock-token={lock_token}&additional-ttl={additional_ttl}"
        )

        # Should be a 200 OK
        if response.status_code != 200:
            msg = f"Oopsie, status code 200 was awaited, received {response.status_code}."
            pytest.fail(msg)

        # Response should contain expected fields
        response_dict = response.json()
        if "message" not in response_dict:
            pytest.fail("Response should contain 'message' field")
        if "new-expires-at" not in response_dict:
            pytest.fail("Response should contain 'new-expires-at' field")
        if "total-lock-duration" not in response_dict:
            pytest.fail("Response should contain 'total-lock-duration' field")

    def test_extend_lock_invalid_token(self, app):
        """
        Title: Extend a lock with invalid token.

        Given: A resource exists.
        And: The resource is locked.
        When: Requesting to extend the lock with an invalid token.
        Then: A 403 Forbidden status code is returned.
        """
        # Reset Database
        reset_database()

        # Add a resource to memory
        import rentabot.models
        from rentabot.models import resources_by_id

        resource = Resource(id=1, name="resource", description="I'm a resource!")
        resource = resource.model_copy(update={"max_lock_duration": 7200})
        resources_by_id[1] = resource
        rentabot.models.next_resource_id = 2

        # Lock the resource
        response = app.post("/api/v1/resources/1/lock")
        if response.status_code != 200:
            msg = f"Oopsie, lock failed with status code {response.status_code}."
            pytest.fail(msg)

        # Try to extend with invalid token
        invalid_token = "verybadtokenbadbadbad"
        response = app.post(
            f"/api/v1/resources/1/extend?lock-token={invalid_token}&additional-ttl=600"
        )

        # Should be a 403 Forbidden
        if response.status_code != 403:
            msg = f"Oopsie, status code 403 was awaited, received {response.status_code}."
            pytest.fail(msg)

    def test_extend_lock_unlocked_resource(self, app):
        """
        Title: Extend a lock on unlocked resource.

        Given: A resource exists.
        And: The resource is not locked.
        When: Requesting to extend the lock.
        Then: A 403 Forbidden status code is returned.
        """
        # Reset Database
        reset_database()

        # Add a resource to memory
        import rentabot.models
        from rentabot.models import resources_by_id

        resource = Resource(id=1, name="resource", description="I'm a resource!")
        resource = resource.model_copy(update={"max_lock_duration": 7200})
        resources_by_id[1] = resource
        rentabot.models.next_resource_id = 2

        # Try to extend without locking first
        response = app.post("/api/v1/resources/1/extend?lock-token=anytoken&additional-ttl=600")

        # Should be a 403 Forbidden
        if response.status_code != 403:
            msg = f"Oopsie, status code 403 was awaited, received {response.status_code}."
            pytest.fail(msg)

    def test_extend_lock_resource_not_found(self, app):
        """
        Title: Extend a lock on non-existent resource.

        Given: A resource does not exist.
        When: Requesting to extend a lock on this resource.
        Then: A 404 Not Found status code is returned.
        """
        # Reset Database
        reset_database()

        # Add a resource to memory
        import rentabot.models
        from rentabot.models import resources_by_id

        resource = Resource(id=1, name="resource", description="I'm a resource!")
        resources_by_id[1] = resource
        rentabot.models.next_resource_id = 2

        # Try to extend a non-existent resource
        resource_id = 100000
        response = app.post(
            f"/api/v1/resources/{resource_id}/extend?lock-token=anytoken&additional-ttl=600"
        )

        # Should be a 404 Not Found
        if response.status_code != 404:
            msg = f"Oopsie, status code 404 was awaited, received {response.status_code}."
            pytest.fail(msg)

        # Check that the 404 returned is the app 404 and not a generic one
        response_json = response.json()
        assert response_json["resource_id"] == resource_id

    def test_extend_lock_exceeds_max_duration(self, app):
        """
        Title: Extend a lock beyond maximum duration.

        Given: A resource exists with a max lock duration.
        And: The resource is locked.
        When: Requesting to extend the lock beyond the maximum duration.
        Then: A 400 Bad Request status code is returned.
        """
        # Reset Database
        reset_database()

        # Add a resource to memory
        import rentabot.models
        from rentabot.models import resources_by_id

        resource = Resource(id=1, name="resource", description="I'm a resource!")
        resource = resource.model_copy(update={"max_lock_duration": 7200})  # 2 hours max
        resources_by_id[1] = resource
        rentabot.models.next_resource_id = 2

        # Lock the resource with initial TTL
        response = app.post("/api/v1/resources/1/lock?ttl=3600")  # 1 hour
        if response.status_code != 200:
            msg = f"Oopsie, lock failed with status code {response.status_code}."
            pytest.fail(msg)

        lock_token = response.json()["lock-token"]

        # Try to extend by excessive amount (total would exceed max_lock_duration)
        excessive_ttl = 10000  # Would result in total > 7200
        response = app.post(
            f"/api/v1/resources/1/extend?lock-token={lock_token}&additional-ttl={excessive_ttl}"
        )

        # Should be a 400 Bad Request
        if response.status_code != 400:
            msg = f"Oopsie, status code 400 was awaited, received {response.status_code}."
            pytest.fail(msg)
