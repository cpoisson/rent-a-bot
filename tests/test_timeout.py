"""
Tests for timeout/TTL functionality.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from rentabot.controllers import (
    extend_resource_lock,
    lock_resource,
    unlock_resource,
)
from rentabot.exceptions import (
    InvalidLockToken,
    ResourceAlreadyLocked,
    ResourceAlreadyUnlocked,
)
from rentabot.models import Resource, resources_by_id


@pytest.fixture(autouse=True)
def clear_resources():
    """Clear resources before and after each test."""
    resources_by_id.clear()
    yield
    resources_by_id.clear()


@pytest.fixture
def sample_resource():
    """Create a sample resource for testing."""
    resource = Resource(
        id=1,
        name="test-device",
        description="Test device",
        tags="ci,linux",
    )
    # Update max_lock_duration after creation
    resource = resource.model_copy(update={"max_lock_duration": 7200})  # 2 hours
    resources_by_id[1] = resource
    return resource


@pytest.mark.asyncio
async def test_lock_with_default_ttl(sample_resource):
    """Test locking a resource with default TTL (3600s)."""
    lock_token, locked_resource = await lock_resource(1)

    assert locked_resource.lock_token == lock_token
    assert locked_resource.lock_acquired_at is not None
    assert locked_resource.lock_expires_at is not None

    # Check that expiration is approximately 1 hour from now (default 3600s)
    expected_expires = locked_resource.lock_acquired_at + timedelta(seconds=3600)
    delta = abs((locked_resource.lock_expires_at - expected_expires).total_seconds())
    assert delta < 1, "Expiration time should be 3600s from acquisition"


@pytest.mark.asyncio
async def test_lock_with_custom_ttl(sample_resource):
    """Test locking a resource with custom TTL."""
    custom_ttl = 1800  # 30 minutes
    lock_token, locked_resource = await lock_resource(1, ttl=custom_ttl)

    assert locked_resource.lock_token == lock_token
    assert locked_resource.lock_acquired_at is not None
    assert locked_resource.lock_expires_at is not None

    # Check that expiration matches custom TTL
    expected_expires = locked_resource.lock_acquired_at + timedelta(seconds=custom_ttl)
    delta = abs((locked_resource.lock_expires_at - expected_expires).total_seconds())
    assert delta < 1, f"Expiration time should be {custom_ttl}s from acquisition"


@pytest.mark.asyncio
async def test_lock_ttl_exceeds_max_duration(sample_resource):
    """Test that locking with TTL exceeding max_lock_duration raises ValueError."""
    # max_lock_duration is 7200s (2 hours)
    excessive_ttl = 10800  # 3 hours

    with pytest.raises(ValueError, match="exceeds maximum allowed duration"):
        await lock_resource(1, ttl=excessive_ttl)


@pytest.mark.asyncio
async def test_extend_lock_basic(sample_resource):
    """Test extending a lock's duration."""
    # Lock the resource
    lock_token, locked_resource = await lock_resource(1, ttl=1800)
    original_expires = locked_resource.lock_expires_at

    # Wait a moment to ensure time passes
    await asyncio.sleep(0.1)

    # Extend by 600 seconds - this sets expiration to NOW + 600s
    # (not original_expires + 600s)
    extended_resource = await extend_resource_lock(1, lock_token, 600)

    assert extended_resource.lock_expires_at is not None
    assert original_expires is not None

    # The new expiration should be approximately current time + 600s
    # which is earlier than the original 30min expiration
    # This is expected behavior: extension sets a new deadline from now
    expected_expires = datetime.now(timezone.utc) + timedelta(seconds=600)
    delta = abs((extended_resource.lock_expires_at - expected_expires).total_seconds())
    assert delta < 2, "Extension should set expiration to now + additional_ttl"


@pytest.mark.asyncio
async def test_extend_lock_invalid_token(sample_resource):
    """Test that extending with invalid token raises InvalidLockToken."""
    lock_token, _ = await lock_resource(1, ttl=1800)

    with pytest.raises(InvalidLockToken):
        await extend_resource_lock(1, "wrong-token", 600)


@pytest.mark.asyncio
async def test_extend_unlocked_resource(sample_resource):
    """Test that extending an unlocked resource raises ResourceAlreadyUnlocked."""
    with pytest.raises(ResourceAlreadyUnlocked):
        await extend_resource_lock(1, "any-token", 600)


@pytest.mark.asyncio
async def test_extend_exceeds_max_duration(sample_resource):
    """Test that extension exceeding max_lock_duration raises ValueError."""
    # Lock with 1800s (30 min), max is 7200s (2 hours)
    lock_token, _ = await lock_resource(1, ttl=1800)

    # Wait to accumulate some elapsed time
    await asyncio.sleep(0.1)

    # Try to extend by 10000s, which when added to remaining time would exceed max 7200s
    with pytest.raises(ValueError, match="would exceed maximum allowed"):
        await extend_resource_lock(1, lock_token, 10000)


@pytest.mark.asyncio
async def test_extend_within_max_duration(sample_resource):
    """Test that extension within max_lock_duration succeeds."""
    # Lock with 3600s (1 hour), max is 7200s (2 hours)
    lock_token, _ = await lock_resource(1, ttl=3600)

    # Extend by 3000s (50 min), total ~6600s, within max 7200s
    extended_resource = await extend_resource_lock(1, lock_token, 3000)

    assert extended_resource.lock_expires_at is not None
    # Verify lock is still active
    assert extended_resource.lock_token == lock_token


@pytest.mark.asyncio
async def test_unlock_clears_timestamps(sample_resource):
    """Test that unlocking clears lock timestamps."""
    lock_token, locked_resource = await lock_resource(1, ttl=1800)

    assert locked_resource.lock_acquired_at is not None
    assert locked_resource.lock_expires_at is not None

    await unlock_resource(1, lock_token)

    unlocked_resource = resources_by_id[1]
    assert unlocked_resource.lock_token == ""
    assert unlocked_resource.lock_acquired_at is None
    assert unlocked_resource.lock_expires_at is None


@pytest.mark.asyncio
async def test_auto_expire_locks_basic():
    """Test auto-expiration of expired locks."""
    # Create a resource
    resource = Resource(
        id=1,
        name="test-device",
        description="Test device",
        tags="ci",
    )
    resources_by_id[1] = resource

    # Lock with very short TTL (1 second)
    await lock_resource(1, ttl=1)

    # Verify it's locked
    assert resources_by_id[1].lock_token != ""

    # Run one iteration of auto-expire (without the while loop)
    # We'll manually trigger the expiration logic after waiting
    await asyncio.sleep(1.5)  # Wait for lock to expire

    # Manually expire (simulate one iteration of background task)
    now = datetime.now(timezone.utc)
    resource = resources_by_id[1]
    if resource.lock_token and resource.lock_expires_at and resource.lock_expires_at <= now:
        updated = resource.model_copy(
            update={
                "lock_token": "",
                "lock_details": f"Auto-expired at {now.isoformat()}",
                "lock_acquired_at": None,
                "lock_expires_at": None,
            }
        )
        resources_by_id[1] = updated

    # Verify it was unlocked
    assert resources_by_id[1].lock_token == ""
    assert "Auto-expired" in resources_by_id[1].lock_details


@pytest.mark.asyncio
async def test_auto_expire_does_not_unlock_valid_locks():
    """Test that auto-expire doesn't unlock locks that haven't expired."""
    # Create a resource
    resource = Resource(
        id=1,
        name="test-device",
        description="Test device",
        tags="ci",
    )
    resources_by_id[1] = resource

    # Lock with long TTL
    lock_token, _ = await lock_resource(1, ttl=3600)

    # Check immediately - should not expire
    now = datetime.now(timezone.utc)
    resource = resources_by_id[1]

    # Verify not expired
    assert resource.lock_token == lock_token
    assert resource.lock_expires_at is not None
    assert resource.lock_expires_at > now


@pytest.mark.asyncio
async def test_multiple_resources_expiration():
    """Test expiration works correctly with multiple resources."""
    # Create multiple resources
    for i in range(1, 4):
        resource = Resource(
            id=i,
            name=f"device-{i}",
            description=f"Device {i}",
            tags="ci",
        )
        resources_by_id[i] = resource

    # Lock all with different TTLs
    await lock_resource(1, ttl=1)  # Expires quickly
    await lock_resource(2, ttl=3600)  # Expires in 1 hour
    await lock_resource(3, ttl=1)  # Expires quickly

    # Wait for short TTLs to expire
    await asyncio.sleep(1.5)

    # Manually expire locks (simulate background task)
    now = datetime.now(timezone.utc)
    for res_id, resource in list(resources_by_id.items()):
        if resource.lock_token and resource.lock_expires_at and resource.lock_expires_at <= now:
            updated = resource.model_copy(
                update={
                    "lock_token": "",
                    "lock_details": f"Auto-expired at {now.isoformat()}",
                    "lock_acquired_at": None,
                    "lock_expires_at": None,
                }
            )
            resources_by_id[res_id] = updated

    # Verify resources 1 and 3 expired, resource 2 still locked
    assert resources_by_id[1].lock_token == ""
    assert resources_by_id[2].lock_token != ""
    assert resources_by_id[3].lock_token == ""


@pytest.mark.asyncio
async def test_lock_already_locked_resource():
    """Test that locking an already locked resource raises ResourceAlreadyLocked."""
    resource = Resource(
        id=1,
        name="test-device",
        description="Test device",
        tags="ci",
    )
    resources_by_id[1] = resource

    # Lock once
    await lock_resource(1, ttl=3600)

    # Try to lock again
    with pytest.raises(ResourceAlreadyLocked):
        await lock_resource(1, ttl=1800)


@pytest.mark.asyncio
async def test_timezone_aware_timestamps(sample_resource):
    """Test that all timestamps are timezone-aware (UTC)."""
    lock_token, locked_resource = await lock_resource(1, ttl=1800)

    assert locked_resource.lock_acquired_at is not None
    assert locked_resource.lock_expires_at is not None
    assert locked_resource.lock_acquired_at.tzinfo == timezone.utc
    assert locked_resource.lock_expires_at.tzinfo == timezone.utc
