"""
Reservations Functional Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains Rent-A-Bot Reservations functional requirements.

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

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from rentabot.exceptions import InsufficientResources
from rentabot.main import app
from rentabot.models import reservations_by_id, resources_by_id

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage():
    resources_by_id.clear()
    reservations_by_id.clear()
    yield
    resources_by_id.clear()
    reservations_by_id.clear()


@pytest.fixture
def setup_resources():
    from rentabot.models import Resource

    resources = [
        Resource(id=1, name="device-1", tags="ci,linux"),
        Resource(id=2, name="device-2", tags="ci,linux"),
        Resource(id=3, name="device-3", tags="ci,windows"),
    ]
    for resource in resources:
        resources_by_id[resource.id] = resource
    return resources


class TestCreateReservation:
    """
    Title: Create a reservation for resources matching given tags.

    As: An automation developer.
    I want: To create a reservation for resources matching specific tags.
    So that: I can be queued to receive resources when they become available.
    """

    def test_create_reservation_api(self, setup_resources):
        """
        Title: Create a reservation via the API.

        Given: Resources matching the requested tags exist.
        And: A valid quantity, max_wait_time and ttl are provided.
        When: Posting a reservation request to the API.
        Then: A reservation is created with status pending and the correct attributes.
        """
        response = client.post(
            "/api/v1/reservations",
            json={"tags": ["ci", "linux"], "quantity": 2, "max_wait_time": 1800, "ttl": 3600},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["tags"] == ["ci", "linux"]
        assert data["quantity"] == 2
        assert data["reservation_id"].startswith("res_")

    def test_create_reservation_no_matching_resources(self):
        """
        Title: Attempt to create a reservation when no resources match the tags.

        Given: Only resources with tags not matching the requested tags exist.
        When: Posting a reservation request for tags with no matching resources.
        Then: The API returns a 404 Not Found response.
        """
        from rentabot.models import Resource

        # Add only Linux resources
        resources_by_id[1] = Resource(id=1, name="device-1", tags="ci,linux")

        # Try to create reservation for Windows
        response = client.post(
            "/api/v1/reservations", json={"tags": ["ci", "windows"], "quantity": 1}
        )

        assert response.status_code == 404

    def test_create_reservation_invalid_quantity(self):
        """
        Title: Attempt to create a reservation with an invalid quantity.

        Given: A resource matching the requested tags exists.
        And: The quantity provided is zero.
        When: Posting the reservation request.
        Then: The API returns a 422 Unprocessable Entity response.
        """
        from rentabot.models import Resource

        # Add a resource first so it doesn't fail with 404
        resources_by_id[1] = Resource(id=1, name="device-1", tags="ci,linux")

        response = client.post(
            "/api/v1/reservations", json={"tags": ["ci", "linux"], "quantity": 0}
        )

        # Should fail validation - quantity must be > 0
        assert response.status_code == 422


class TestGetReservation:
    """
    Title: Retrieve reservation information.

    As: An automation developer.
    I want: To retrieve information about existing reservations.
    So that: I can track the status and position of my reservations in the queue.
    """

    def test_get_reservation_api(self, setup_resources):
        """
        Title: Retrieve a specific reservation by its ID.

        Given: A reservation has been created.
        When: Requesting the reservation by its ID.
        Then: The reservation details are returned with the correct status and queue position.
        """
        # Create reservation
        create_response = client.post(
            "/api/v1/reservations", json={"tags": ["ci", "linux"], "quantity": 1}
        )
        reservation_id = create_response.json()["reservation_id"]

        # Get reservation
        response = client.get(f"/api/v1/reservations/{reservation_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["reservation_id"] == reservation_id
        assert data["status"] == "pending"
        assert data["position_in_queue"] == 1

    def test_get_reservation_not_found_api(self):
        """
        Title: Attempt to retrieve a reservation that does not exist.

        Given: No reservation exists with the requested ID.
        When: Requesting a reservation by a non-existent ID.
        Then: The API returns a 404 Not Found response.
        """
        response = client.get("/api/v1/reservations/res_nonexistent")
        assert response.status_code == 404

    def test_list_reservations_api(self, setup_resources):
        """
        Title: List all existing reservations.

        Given: Multiple reservations have been created.
        When: Requesting the list of all reservations.
        Then: All created reservations are returned.
        """
        # Create multiple reservations
        client.post("/api/v1/reservations", json={"tags": ["ci", "linux"], "quantity": 1})
        client.post("/api/v1/reservations", json={"tags": ["ci", "windows"], "quantity": 1})

        # List all
        response = client.get("/api/v1/reservations")

        assert response.status_code == 200
        data = response.json()
        assert len(data["reservations"]) == 2

    def test_list_reservations_empty(self):
        """
        Title: List reservations when none exist.

        Given: No reservations exist.
        When: Requesting the list of all reservations.
        Then: An empty list is returned.
        """
        response = client.get("/api/v1/reservations")

        assert response.status_code == 200
        data = response.json()
        assert data["reservations"] == []


class TestCancelReservation:
    """
    Title: Cancel a pending reservation.

    As: An automation developer.
    I want: To cancel a reservation I no longer need.
    So that: The queued slot is freed and resources are not needlessly held.
    """

    def test_cancel_reservation_api(self, setup_resources):
        """
        Title: Cancel a pending reservation via the API.

        Given: A pending reservation exists.
        When: Sending a DELETE request for that reservation.
        Then: The reservation is removed and subsequent GET returns 404.
        """
        # Create reservation
        create_response = client.post(
            "/api/v1/reservations", json={"tags": ["ci", "linux"], "quantity": 1}
        )
        reservation_id = create_response.json()["reservation_id"]

        # Cancel reservation
        response = client.delete(f"/api/v1/reservations/{reservation_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/reservations/{reservation_id}")
        assert get_response.status_code == 404

    def test_cancel_fulfilled_reservation_fails(self, setup_resources):
        """
        Title: Attempt to cancel a fulfilled reservation.

        Given: A reservation exists and has been fulfilled.
        When: Sending a DELETE request for that reservation.
        Then: The API returns a 409 Conflict response.
        """
        # Create and manually fulfill a reservation
        create_response = client.post(
            "/api/v1/reservations", json={"tags": ["ci", "linux"], "quantity": 1}
        )
        reservation_id = create_response.json()["reservation_id"]

        # Manually mark as fulfilled
        now = datetime.now(timezone.utc)
        reservations_by_id[reservation_id] = reservations_by_id[reservation_id].model_copy(
            update={
                "status": "fulfilled",
                "fulfilled_at": now,
                "claim_expires_at": now + timedelta(seconds=60),
            }
        )

        # Try to cancel
        response = client.delete(f"/api/v1/reservations/{reservation_id}")
        assert response.status_code == 409  # Conflict


class TestClaimReservation:
    """
    Title: Claim a fulfilled reservation to obtain the allocated resources.

    As: An automation developer.
    I want: To claim a fulfilled reservation.
    So that: I can use the allocated resources for my automation tasks.
    """

    def test_claim_reservation_api(self, setup_resources):
        """
        Title: Claim a fulfilled reservation via the API.

        Given: A reservation exists and has been fulfilled with allocated resources.
        And: The claim window has not expired.
        When: Sending a POST claim request for that reservation.
        Then: The reservation status changes to claimed and claimed_at is set.
        """
        # Create reservation
        create_response = client.post(
            "/api/v1/reservations", json={"tags": ["ci", "linux"], "quantity": 1}
        )
        reservation_id = create_response.json()["reservation_id"]

        # Manually fulfill it
        now = datetime.now(timezone.utc)
        reservations_by_id[reservation_id] = reservations_by_id[reservation_id].model_copy(
            update={
                "status": "fulfilled",
                "fulfilled_at": now,
                "claim_expires_at": now + timedelta(seconds=60),
                "resource_ids": [1],
                "lock_tokens": ["token-123"],
            }
        )

        # Claim it
        response = client.post(f"/api/v1/reservations/{reservation_id}/claim")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "claimed"
        assert data["claimed_at"] is not None

    def test_claim_pending_reservation_fails(self, setup_resources):
        """
        Title: Attempt to claim a reservation that is still pending.

        Given: A reservation exists with status pending.
        When: Sending a POST claim request for that reservation.
        Then: The API returns a 409 Conflict response.
        """
        # Create reservation
        create_response = client.post(
            "/api/v1/reservations", json={"tags": ["ci", "linux"], "quantity": 1}
        )
        reservation_id = create_response.json()["reservation_id"]

        # Try to claim while still pending
        response = client.post(f"/api/v1/reservations/{reservation_id}/claim")
        assert response.status_code == 409  # Conflict

    def test_claim_expired_reservation_fails(self, setup_resources):
        """
        Title: Attempt to claim a reservation whose claim window has expired.

        Given: A reservation exists with status fulfilled.
        And: The claim expiry time is in the past.
        When: Sending a POST claim request for that reservation.
        Then: The API returns a 410 Gone response.
        """
        # Create reservation
        create_response = client.post(
            "/api/v1/reservations", json={"tags": ["ci", "linux"], "quantity": 1}
        )
        reservation_id = create_response.json()["reservation_id"]

        # Manually fulfill with expired claim window
        past = datetime.now(timezone.utc) - timedelta(seconds=120)
        reservations_by_id[reservation_id] = reservations_by_id[reservation_id].model_copy(
            update={
                "status": "fulfilled",
                "fulfilled_at": past,
                "claim_expires_at": past + timedelta(seconds=60),
                "resource_ids": [1],
                "lock_tokens": ["token-123"],
            }
        )

        # Try to claim
        response = client.post(f"/api/v1/reservations/{reservation_id}/claim")
        assert response.status_code == 410  # Gone


class TestReservationLifecycle:
    """
    Title: End-to-end and concurrent reservation lifecycle.

    As: An automation developer.
    I want: Reservations to follow a correct lifecycle and respect FIFO ordering.
    So that: Resources are allocated fairly and workflows complete successfully.
    """

    @pytest.mark.asyncio
    async def test_end_to_end_reservation_workflow(self, setup_resources):
        """
        Title: Complete reservation workflow from creation to resource release.

        Given: Resources matching the requested tags exist.
        And: All matching resources are initially locked.
        When: Creating a reservation, unlocking a resource, fulfilling and claiming the reservation.
        Then: The reservation transitions through pending, fulfilled and claimed states and the resource is released after use.
        """
        from rentabot.controllers import lock_resources_by_tags

        # 1. Lock all resources to start
        locked = await lock_resources_by_tags(["ci", "linux"], 2, ttl=3600)

        # 2. Create reservation (should be pending)
        create_response = client.post(
            "/api/v1/reservations", json={"tags": ["ci", "linux"], "quantity": 1, "ttl": 1800}
        )
        assert create_response.status_code == 201
        reservation_id = create_response.json()["reservation_id"]

        # Verify it's pending
        get_response = client.get(f"/api/v1/reservations/{reservation_id}")
        assert get_response.json()["status"] == "pending"

        # 3. Unlock one resource
        from rentabot.controllers import unlock_resource_by_token

        await unlock_resource_by_token(locked[0].lock_token)

        # 4. Run one iteration of fulfillment (simulate background task)
        # We can't easily test the background task, so we'll manually trigger fulfillment
        from rentabot.controllers import get_reservation as get_res

        reservation = await get_res(reservation_id)
        if reservation.status == "pending":
            try:
                locked_for_res = await lock_resources_by_tags(
                    reservation.tags, reservation.quantity, reservation.ttl
                )
                now = datetime.now(timezone.utc)
                reservations_by_id[reservation_id] = reservation.model_copy(
                    update={
                        "status": "fulfilled",
                        "fulfilled_at": now,
                        "claim_expires_at": now + timedelta(seconds=60),
                        "resource_ids": [r.id for r in locked_for_res],
                        "lock_tokens": [r.lock_token for r in locked_for_res],
                    }
                )
            except InsufficientResources:
                # If insufficient resources, reservation remains pending (expected behavior)
                pass

        # 5. Verify it's fulfilled
        get_response = client.get(f"/api/v1/reservations/{reservation_id}")
        data = get_response.json()
        assert data["status"] == "fulfilled"
        assert len(data["resource_ids"]) == 1

        # 6. Claim the reservation
        claim_response = client.post(f"/api/v1/reservations/{reservation_id}/claim")
        assert claim_response.status_code == 200
        assert claim_response.json()["status"] == "claimed"

        # 7. Verify we can unlock using the token
        token = data["lock_tokens"][0]
        await unlock_resource_by_token(token)

        # Resource should be unlocked now
        from rentabot.controllers import get_resource_from_id

        resource = get_resource_from_id(data["resource_ids"][0])
        assert resource.lock_token == ""

    @pytest.mark.asyncio
    async def test_concurrent_reservations_fifo(self, setup_resources):
        """
        Title: Multiple concurrent reservations are queued in FIFO order.

        Given: Resources matching the requested tags exist.
        And: Multiple reservations are created in sequence.
        When: Checking the position in queue for each reservation.
        Then: Reservations are positioned in the order they were created.
        """
        # Create 3 reservations
        res_ids = []
        for _ in range(3):
            response = client.post(
                "/api/v1/reservations", json={"tags": ["ci", "linux"], "quantity": 1}
            )
            res_ids.append(response.json()["reservation_id"])
            await asyncio.sleep(0.01)  # Ensure different timestamps

        # Check positions
        for i, res_id in enumerate(res_ids):
            response = client.get(f"/api/v1/reservations/{res_id}")
            assert response.json()["position_in_queue"] == i + 1


class TestReservationCleanup:
    """
    Title: Automatic cleanup of expired and unclaimed reservations.

    As: A system operator.
    I want: Stale reservations to be removed and their resources released automatically.
    So that: The system does not accumulate outdated reservations or hold resources unnecessarily.
    """

    @pytest.mark.asyncio
    async def test_reservation_cleanup_expired_pending(self):
        """
        Title: Expired pending reservations are removed during cleanup.

        Given: A pending reservation with a very short max_wait_time exists.
        And: The reservation has passed its expiry time.
        When: The cleanup logic runs.
        Then: The expired pending reservation is removed and returns 404.
        """
        from rentabot.models import Resource

        resources_by_id[1] = Resource(id=1, name="device-1", tags="ci,linux")

        # Create reservation with very short max_wait_time
        response = client.post(
            "/api/v1/reservations",
            json={"tags": ["ci", "linux"], "quantity": 1, "max_wait_time": 1},
        )
        reservation_id = response.json()["reservation_id"]

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Manually run cleanup logic (simulate background task)
        now = datetime.now(timezone.utc)
        for res_id, reservation in list(reservations_by_id.items()):
            if reservation.status == "pending" and reservation.expires_at <= now:
                del reservations_by_id[res_id]

        # Verify it's gone
        response = client.get(f"/api/v1/reservations/{reservation_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reservation_cleanup_expired_unclaimed(self):
        """
        Title: Unclaimed fulfilled reservations are cleaned up and their resources unlocked.

        Given: A fulfilled reservation whose claim window has expired exists.
        And: The reservation holds locked resources.
        When: The cleanup logic runs.
        Then: The reservation is removed and the previously locked resources are unlocked.
        """
        from rentabot.models import Resource

        resources_by_id[1] = Resource(id=1, name="device-1", tags="ci,linux")

        # Create and fulfill a reservation
        response = client.post(
            "/api/v1/reservations", json={"tags": ["ci", "linux"], "quantity": 1}
        )
        reservation_id = response.json()["reservation_id"]

        # Manually fulfill with expired claim window
        past = datetime.now(timezone.utc) - timedelta(seconds=120)
        from rentabot.controllers import lock_resources_by_tags

        locked = await lock_resources_by_tags(["ci", "linux"], 1)

        reservations_by_id[reservation_id] = reservations_by_id[reservation_id].model_copy(
            update={
                "status": "fulfilled",
                "fulfilled_at": past,
                "claim_expires_at": past + timedelta(seconds=60),
                "resource_ids": [r.id for r in locked],
                "lock_tokens": [r.lock_token for r in locked],
            }
        )

        # Manually run cleanup (simulate background task)
        now = datetime.now(timezone.utc)
        for res_id, reservation in list(reservations_by_id.items()):
            if (
                reservation.status == "fulfilled"
                and reservation.claim_expires_at
                and reservation.claim_expires_at <= now
            ):
                # Unlock resources
                from rentabot.controllers import unlock_resource_by_token

                for token in reservation.lock_tokens:
                    try:
                        await unlock_resource_by_token(token)
                    except Exception:
                        # Best-effort cleanup: ignore unlock failures (e.g., already unlocked or invalid token).
                        pass
                del reservations_by_id[res_id]

        # Verify reservation is gone
        response = client.get(f"/api/v1/reservations/{reservation_id}")
        assert response.status_code == 404

        # Verify resources are unlocked
        from rentabot.controllers import get_resource_from_id

        for res_id in [r.id for r in locked]:
            resource = get_resource_from_id(res_id)
            assert resource.lock_token == ""
