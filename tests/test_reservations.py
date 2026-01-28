"""
Unit tests for reservation functionality.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from rentabot.controllers import (
    cancel_reservation,
    claim_reservation,
    create_reservation,
    get_reservation,
    list_reservations,
    lock_resources_by_tags,
)
from rentabot.exceptions import (
    InsufficientResources,
    InvalidReservationTags,
    ReservationCannotBeCancelled,
    ReservationClaimExpired,
    ReservationNotFound,
    ReservationNotFulfilled,
    ResourceNotFound,
)
from rentabot.models import (
    Resource,
    reservations_by_id,
    resources_by_id,
)


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear resources and reservations before and after each test."""
    resources_by_id.clear()
    reservations_by_id.clear()
    yield
    resources_by_id.clear()
    reservations_by_id.clear()


@pytest.fixture
def sample_resources():
    """Create sample resources for testing."""
    resources = [
        Resource(id=1, name="device-1", description="Linux CI machine", tags="ci,linux"),
        Resource(id=2, name="device-2", description="Linux CI machine", tags="ci,linux"),
        Resource(id=3, name="device-3", description="Windows machine", tags="ci,windows"),
        Resource(id=4, name="device-4", description="Linux CI machine", tags="ci,linux"),
    ]
    for resource in resources:
        resources_by_id[resource.id] = resource
    return resources


@pytest.mark.asyncio
async def test_create_reservation_basic(sample_resources):
    """Test creating a basic reservation."""
    reservation = await create_reservation(tags=["ci", "linux"], quantity=2)

    assert reservation.reservation_id.startswith("res_")
    assert reservation.status == "pending"
    assert reservation.tags == ["ci", "linux"]
    assert reservation.quantity == 2
    assert reservation.ttl == 3600  # default
    assert reservation.created_at is not None
    assert reservation.expires_at is not None
    assert (reservation.expires_at - reservation.created_at).total_seconds() == 3600


@pytest.mark.asyncio
async def test_create_reservation_custom_params(sample_resources):
    """Test creating a reservation with custom parameters."""
    reservation = await create_reservation(
        tags=["ci", "windows"], quantity=1, max_wait_time=1800, ttl=7200
    )

    assert reservation.status == "pending"
    assert reservation.tags == ["ci", "windows"]
    assert reservation.quantity == 1
    assert reservation.ttl == 7200
    assert (reservation.expires_at - reservation.created_at).total_seconds() == 1800


@pytest.mark.asyncio
async def test_create_reservation_no_matching_resources():
    """Test that creating a reservation with no matching resources raises error."""
    resource = Resource(id=1, name="device-1", tags="ci,linux")
    resources_by_id[1] = resource

    with pytest.raises(ResourceNotFound, match="No resources match"):
        await create_reservation(tags=["windows"], quantity=1)


@pytest.mark.asyncio
async def test_create_reservation_empty_tags():
    """Test that creating a reservation with empty tags raises error."""
    resource = Resource(id=1, name="device-1", tags="ci,linux")
    resources_by_id[1] = resource

    with pytest.raises(InvalidReservationTags, match="Tags list cannot be empty"):
        await create_reservation(tags=[], quantity=1)


@pytest.mark.asyncio
async def test_create_reservation_insufficient_total_resources():
    """Test that reservation is rejected when not enough compatible resources exist."""
    from rentabot.exceptions import InvalidTTL

    # Create only 1 Windows machine with specific max_lock_duration
    resource = Resource(id=1, name="device-1", tags="ci,windows", max_lock_duration=7200)
    resources_by_id[1] = resource

    # Request 2 resources - should fail TTL validation since only 1 exists
    with pytest.raises(InvalidTTL, match="Need 2 compatible resources, found 1"):
        await create_reservation(tags=["ci", "windows"], quantity=2, ttl=3600)


@pytest.mark.asyncio
async def test_get_reservation(sample_resources):
    """Test getting a reservation by ID."""
    created = await create_reservation(tags=["ci", "linux"], quantity=1)

    retrieved = await get_reservation(created.reservation_id)

    assert retrieved.reservation_id == created.reservation_id
    assert retrieved.status == "pending"
    assert retrieved.position_in_queue == 1


@pytest.mark.asyncio
async def test_get_reservation_not_found():
    """Test getting a non-existent reservation."""
    with pytest.raises(ReservationNotFound):
        await get_reservation("res_nonexistent")


@pytest.mark.asyncio
async def test_get_reservation_position_in_queue(sample_resources):
    """Test that position in queue is calculated correctly."""
    # Create 3 reservations
    res1 = await create_reservation(tags=["ci", "linux"], quantity=1)
    await asyncio.sleep(0.01)  # Ensure different timestamps
    res2 = await create_reservation(tags=["ci", "linux"], quantity=1)
    await asyncio.sleep(0.01)
    res3 = await create_reservation(tags=["ci", "linux"], quantity=1)

    # Check positions (FIFO)
    r1 = await get_reservation(res1.reservation_id)
    r2 = await get_reservation(res2.reservation_id)
    r3 = await get_reservation(res3.reservation_id)

    assert r1.position_in_queue == 1
    assert r2.position_in_queue == 2
    assert r3.position_in_queue == 3


@pytest.mark.asyncio
async def test_claim_reservation_not_found():
    """Test claiming a non-existent reservation."""
    with pytest.raises(ReservationNotFound):
        await claim_reservation("res_nonexistent")


@pytest.mark.asyncio
async def test_claim_reservation_not_fulfilled(sample_resources):
    """Test claiming a pending reservation raises error."""
    reservation = await create_reservation(tags=["ci", "linux"], quantity=1)

    with pytest.raises(ReservationNotFulfilled, match="not yet fulfilled"):
        await claim_reservation(reservation.reservation_id)


@pytest.mark.asyncio
async def test_claim_reservation_success(sample_resources):
    """Test successfully claiming a fulfilled reservation."""
    # Create and manually fulfill a reservation
    reservation = await create_reservation(tags=["ci", "linux"], quantity=1)

    # Manually lock a resource and mark reservation as fulfilled
    now = datetime.now(timezone.utc)
    reservations_by_id[reservation.reservation_id] = reservation.model_copy(
        update={
            "status": "fulfilled",
            "fulfilled_at": now,
            "claim_expires_at": now + timedelta(seconds=60),
            "resource_ids": [1],
            "lock_tokens": ["token-123"],
        }
    )

    # Claim it
    claimed = await claim_reservation(reservation.reservation_id)

    assert claimed.status == "claimed"
    assert claimed.claimed_at is not None
    assert claimed.resource_ids == [1]
    assert claimed.lock_tokens == ["token-123"]


@pytest.mark.asyncio
async def test_claim_reservation_expired(sample_resources):
    """Test claiming an expired reservation raises error."""
    reservation = await create_reservation(tags=["ci", "linux"], quantity=1)

    # Manually fulfill with expired claim window
    past_time = datetime.now(timezone.utc) - timedelta(seconds=120)
    reservations_by_id[reservation.reservation_id] = reservation.model_copy(
        update={
            "status": "fulfilled",
            "fulfilled_at": past_time,
            "claim_expires_at": past_time + timedelta(seconds=60),  # Already expired
            "resource_ids": [1],
            "lock_tokens": ["token-123"],
        }
    )

    with pytest.raises(ReservationClaimExpired, match="Claim window has expired"):
        await claim_reservation(reservation.reservation_id)


@pytest.mark.asyncio
async def test_cancel_reservation_pending(sample_resources):
    """Test cancelling a pending reservation."""
    reservation = await create_reservation(tags=["ci", "linux"], quantity=1)

    await cancel_reservation(reservation.reservation_id)

    # Should be removed
    assert reservation.reservation_id not in reservations_by_id


@pytest.mark.asyncio
async def test_cancel_reservation_not_found():
    """Test cancelling a non-existent reservation."""
    with pytest.raises(ReservationNotFound):
        await cancel_reservation("res_nonexistent")


@pytest.mark.asyncio
async def test_cancel_reservation_fulfilled(sample_resources):
    """Test that cancelling a fulfilled reservation raises error."""
    reservation = await create_reservation(tags=["ci", "linux"], quantity=1)

    # Mark as fulfilled
    now = datetime.now(timezone.utc)
    reservations_by_id[reservation.reservation_id] = reservation.model_copy(
        update={
            "status": "fulfilled",
            "fulfilled_at": now,
            "claim_expires_at": now + timedelta(seconds=60),
        }
    )

    with pytest.raises(ReservationCannotBeCancelled, match="Cannot cancel fulfilled"):
        await cancel_reservation(reservation.reservation_id)


@pytest.mark.asyncio
async def test_cancel_reservation_claimed(sample_resources):
    """Test that cancelling a claimed reservation raises error."""
    reservation = await create_reservation(tags=["ci", "linux"], quantity=1)

    # Mark as claimed
    reservations_by_id[reservation.reservation_id] = reservation.model_copy(
        update={"status": "claimed"}
    )

    with pytest.raises(ReservationCannotBeCancelled, match="Cannot cancel claimed"):
        await cancel_reservation(reservation.reservation_id)


@pytest.mark.asyncio
async def test_list_reservations_empty():
    """Test listing reservations when none exist."""
    reservations = await list_reservations()
    assert reservations == []


@pytest.mark.asyncio
async def test_list_reservations_multiple(sample_resources):
    """Test listing multiple reservations."""
    await create_reservation(tags=["ci", "linux"], quantity=1)
    await asyncio.sleep(0.01)
    await create_reservation(tags=["ci", "windows"], quantity=1)

    reservations = await list_reservations()

    assert len(reservations) == 2
    # Check positions are computed
    pending = [r for r in reservations if r.status == "pending"]
    assert all(r.position_in_queue is not None for r in pending)


@pytest.mark.asyncio
async def test_lock_resources_by_tags_basic(sample_resources):
    """Test locking resources by tags."""
    locked = await lock_resources_by_tags(tags=["ci", "linux"], quantity=2, ttl=1800)

    assert len(locked) == 2
    assert all(r.lock_token for r in locked)
    assert all(r.lock_acquired_at is not None for r in locked)
    assert all(r.lock_expires_at is not None for r in locked)

    # Verify resources are locked in storage
    assert resources_by_id[locked[0].id].lock_token != ""
    assert resources_by_id[locked[1].id].lock_token != ""


@pytest.mark.asyncio
async def test_lock_resources_by_tags_insufficient(sample_resources):
    """Test locking when insufficient resources available."""
    # Only 1 Windows machine
    with pytest.raises(InsufficientResources, match="Not enough resources"):
        await lock_resources_by_tags(tags=["ci", "windows"], quantity=2)


@pytest.mark.asyncio
async def test_lock_resources_by_tags_excludes_locked(sample_resources):
    """Test that locked resources are excluded."""
    # Lock 2 resources first
    locked1 = await lock_resources_by_tags(tags=["ci", "linux"], quantity=2)

    # Try to lock 2 more (only 1 Linux machine left)
    with pytest.raises(InsufficientResources):
        await lock_resources_by_tags(tags=["ci", "linux"], quantity=2)

    # But locking 1 should work
    locked2 = await lock_resources_by_tags(tags=["ci", "linux"], quantity=1)
    assert len(locked2) == 1
    assert locked2[0].id not in [r.id for r in locked1]


@pytest.mark.asyncio
async def test_lock_resources_by_tags_no_matching():
    """Test locking when no resources match tags."""
    resource = Resource(id=1, name="device-1", tags="ci,linux")
    resources_by_id[1] = resource

    # No resources with "windows" tag
    with pytest.raises(InsufficientResources):
        await lock_resources_by_tags(tags=["windows"], quantity=1)


@pytest.mark.asyncio
async def test_lock_resources_by_tags_empty_tags_skipped():
    """Test that resources with empty tags are skipped."""
    resources = [
        Resource(id=1, name="device-1", tags="ci,linux"),
        Resource(id=2, name="device-2", tags=""),  # Empty tags
        Resource(id=3, name="device-3", tags="ci,linux"),
    ]
    for resource in resources:
        resources_by_id[resource.id] = resource

    locked = await lock_resources_by_tags(tags=["ci", "linux"], quantity=2)

    # Should lock devices 1 and 3, skip device 2
    assert len(locked) == 2
    assert all(r.id in [1, 3] for r in locked)


@pytest.mark.asyncio
async def test_fifo_ordering_preservation(sample_resources):
    """Test that FIFO ordering is preserved across operations."""
    # Create 5 reservations with slight delays
    reservations = []
    for _ in range(5):
        res = await create_reservation(tags=["ci", "linux"], quantity=1)
        reservations.append(res)
        await asyncio.sleep(0.01)

    # List and verify order
    all_res = await list_reservations()
    positions = [r.position_in_queue for r in all_res]

    assert positions == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_reservation_expires_at_calculation(sample_resources):
    """Test that expires_at is correctly calculated."""
    max_wait = 1800
    reservation = await create_reservation(tags=["ci", "linux"], quantity=1, max_wait_time=max_wait)

    expected_expires = reservation.created_at + timedelta(seconds=max_wait)
    delta = abs((reservation.expires_at - expected_expires).total_seconds())

    assert delta < 1, "expires_at should be created_at + max_wait_time"


@pytest.mark.asyncio
async def test_timezone_aware_timestamps(sample_resources):
    """Test that all reservation timestamps are timezone-aware (UTC)."""
    reservation = await create_reservation(tags=["ci", "linux"], quantity=1)

    assert reservation.created_at.tzinfo == timezone.utc
    assert reservation.expires_at.tzinfo == timezone.utc


@pytest.mark.asyncio
async def test_create_reservation_ttl_exceeds_max_lock_duration():
    """Test that creating a reservation fails if TTL exceeds all matching resources' max_lock_duration."""
    from rentabot.exceptions import InvalidTTL

    # Create resources with limited max_lock_duration
    resource1 = Resource(id=1, name="device-1", tags="gpu", max_lock_duration=3600)
    resource2 = Resource(id=2, name="device-2", tags="gpu", max_lock_duration=3600)
    resources_by_id[1] = resource1
    resources_by_id[2] = resource2

    # Try to create reservation with TTL exceeding max_lock_duration
    with pytest.raises(InvalidTTL, match="exceeds max_lock_duration"):
        await create_reservation(tags=["gpu"], quantity=1, ttl=7200)


@pytest.mark.asyncio
async def test_create_reservation_ttl_partial_compatibility():
    """Test that reservation fails if not enough resources support the TTL."""
    from rentabot.exceptions import InvalidTTL

    # Create resources with different max_lock_duration values
    resource1 = Resource(id=1, name="device-1", tags="gpu", max_lock_duration=3600)
    resource2 = Resource(
        id=2, name="device-2", tags="gpu", max_lock_duration=7200
    )  # Only this one supports 7200
    resources_by_id[1] = resource1
    resources_by_id[2] = resource2

    # Request 2 resources but only 1 can support the TTL
    with pytest.raises(InvalidTTL, match="Need 2 compatible resources, found 1"):
        await create_reservation(tags=["gpu"], quantity=2, ttl=7200)


@pytest.mark.asyncio
async def test_create_reservation_ttl_compatible():
    """Test that reservation succeeds when enough resources support the TTL."""
    # Create resources with sufficient max_lock_duration
    resources = [
        Resource(id=1, name="device-1", tags="gpu", max_lock_duration=7200),
        Resource(id=2, name="device-2", tags="gpu", max_lock_duration=7200),
    ]
    for resource in resources:
        resources_by_id[resource.id] = resource

    # This should succeed
    reservation = await create_reservation(tags=["gpu"], quantity=2, ttl=7200)
    assert reservation.status == "pending"
    assert reservation.ttl == 7200
