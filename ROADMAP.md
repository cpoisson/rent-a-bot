# Development Roadmap to v1.0

## Vision

Rent-A-Bot aims to be a lightweight, platform-agnostic alternative to Jenkins Lockable Resources, LAVA, Testflinger, and GitLab Resource Groups. As a standalone service with no current users, this roadmap embraces breaking changes to establish a solid v1.0 foundation prioritizing production readiness, simplicity, and cross-platform compatibility.

## Priority Features

1. **Lock Timeout/TTL** - Automatic recovery from dead locks
2. **Smart Reservation Queue** - Wait-and-acquire pattern with priority support
3. **N-of-M Resource Allocation** - Request multiple resources matching criteria
4. **Standardized Tag Handling** - Comma-separated tags for consistency
5. **Basic Authentication** - API key-based access control
6. **Optional Persistence** - SQLite backend for production deployments

---

## Phase 1 - Breaking Changes & Foundation (v0.4.0) ✅ COMPLETED

**Target:** Early Q1 2026 | **Completed:** January 2026

### Breaking Changes
- ✅ **Tag Separator Migration**: Change from space-separated (`"ci linux x86"`) to comma-separated (`"ci,linux,x86"`)
  - Update `Resource.tags` parsing in `controllers.py`
  - Maintain backward-compatible parser during transition
  - Update example resource descriptor files

- ✅ **API Path Simplification**: Shorten from `/rentabot/api/v1.0/` to `/api/v1/`
  - More concise and industry-standard
  - Update all endpoint definitions in `main.py`
  - Add redirect from old paths for migration period

### Foundation Improvements
- ✅ Fix Python version requirement to `>=3.10` in `pyproject.toml`
- ✅ Add `/health` endpoint for monitoring (200 OK if service running)
- ✅ Add `/readiness` endpoint for Kubernetes health checks
- ✅ Consolidate exception handlers following DRY principles
- ✅ Replace custom `model_dump_json()` with Pydantic's `model_dump()`

### Documentation
- ✅ Create migration guide for descriptor format changes
- ✅ Update README with new API paths
- ✅ Add examples for comma-separated tags

**Success Criteria:**
- ✅ All tests pass with new tag format
- ✅ API documentation reflects simplified paths
- ✅ Health endpoints return appropriate status codes

---

## Phase 2 - N-of-M Resource Allocation (v0.5.0) 🟡 IN PROGRESS

**Target:** Mid Q1 2026 | **Status:** Core features completed via reservations

### Core Features
- ✅ **Multi-Resource Lock Endpoint**: Implemented via reservations (see Phase 4)
  - Atomic multi-resource locking with automatic rollback
  - Transaction-style all-or-nothing allocation
  - Note: Direct `POST /api/v1/resources/lock` with quantity parameter not yet implemented

- ❌ **Batch Unlock Endpoint**: `POST /api/v1/resources/unlock-batch`
  ```json
  {
    "lock_tokens": ["uuid1", "uuid2"]
  }
  ```
  - Status: Not yet implemented (can unlock individually)

### Implementation Details
- ❌ Extend `lock_resource()` to support quantity parameter (not on direct lock endpoint yet)
- ✅ Implement atomic multi-resource locking using existing `resource_lock` (via reservations)
- ✅ Add validation to ensure sufficient available resources before locking
- ❌ Update web UI to show resource groups and multi-locks

### API Changes
- ❌ Add `quantity` parameter to existing lock endpoints (default: 1)
- ✅ Maintain backward compatibility with single-resource locks
- ✅ Enhance error messages for insufficient resources

**Success Criteria:**
- ✅ Can successfully lock/unlock N resources in single operation (via reservations)
- ✅ Partial failures result in complete rollback
- ❌ Web UI displays grouped resource allocations
- ✅ Test coverage includes edge cases (insufficient resources, partial availability)

---

## Phase 3 - Lock Timeout & Auto-Expiration (v0.6.0) 🟡 IN PROGRESS

**Target:** Late Q1 2026 | **Status:** Core TTL features completed

### Data Model Extensions ✅ COMPLETED
```python
class Resource(BaseModel):
    # ... existing fields ...
    lock_acquired_at: datetime | None = None
    lock_expires_at: datetime | None = None
    max_lock_duration: int = 3600  # seconds, configurable per-resource
```

### Core Features
- ✅ **TTL Support on Lock Requests**: Optional `ttl` parameter (seconds)
  - Configurable default (3600s)
  - Per-resource max TTL limit
  - Validates requested TTL against max allowed

- ✅ **Automatic Expiration**: Background asyncio task
  - Runs every 10 seconds
  - Scans all locked resources for expired locks
  - Auto-unlocks with details: `"Auto-expired at {timestamp}"`
  - Logs expiration events for audit trail

- ✅ **Lock Extension**: `POST /api/v1/resources/{id}/extend`
  - Extend lock duration before expiration
  - Validates extension against max duration

- ❌ **Monitoring Endpoints**:
  - `GET /api/v1/resources/expired` - List recently expired locks (not implemented)
  - ✅ Include expiration time in resource detail responses
  - ❌ Add warning period (5 min before expiration)

### Implementation Details
- ✅ Background task starts with FastAPI lifespan event
- ✅ Graceful handling of timezone-aware datetimes
- ❌ Update web UI to show:
  - ❌ Time remaining for locked resources
  - ❌ Warning indicator when < 5 minutes remain
  - ❌ Auto-refresh every 10 seconds

**Success Criteria:**
- ✅ Locks automatically expire after TTL
- ✅ Background task doesn't block main event loop
- ❌ Web UI shows countdown timer
- ✅ Expired locks are logged with timestamp and original requester

---

## Phase 4 - Smart Reservation Queue (v0.7.0) 🟡 IN PROGRESS

**Target:** Early Q2 2026 | **Status:** FIFO queue completed, priority/WebSocket pending

### Data Model ✅ COMPLETED (FIFO only)
```python
class Reservation(BaseModel):
    id: str  # UUID
    tags: list[str]
    quantity: int
    # priority: int = 5  # NOT YET IMPLEMENTED - currently pure FIFO
    client_id: str
    created_at: datetime
    expires_at: datetime  # reservation itself expires
    status: str  # "pending", "fulfilled", "cancelled", "expired", "claimed"
    ttl: int  # lock TTL when fulfilled
```

### Core Features
- ✅ **Create Reservation**: `POST /api/v1/reservations`
  ```json
  {
    "tags": ["ci", "linux"],
    "quantity": 2,
    "ttl": 3600,
    "client_id": "jenkins-build-123"
  }
  ```
  - Returns reservation ID for tracking
  - Queues if resources not immediately available
  - Note: `priority` parameter not yet supported

- ❌ **Real-Time Notifications**: Not yet implemented
  - WebSocket endpoint: `GET /ws/reservations/{reservation_id}` (planned)
  - Would send message when resources allocated
  - Client must poll status endpoint currently

- ✅ **Queue Management**:
  - ✅ `GET /api/v1/reservations` - List all reservations
  - ✅ `GET /api/v1/reservations/{id}` - Check reservation status
  - ✅ `DELETE /api/v1/reservations/{id}` - Cancel reservation
  - ✅ `POST /api/v1/reservations/{id}/claim` - Claim fulfilled reservation

### Implementation Details
- ✅ **Auto-Fulfillment Task**: Background process
  - Runs every 10 seconds
  - Matches freed resources to pending reservations
  - ✅ Currently: strict FIFO by created_at
  - ❌ Priority sorting not yet implemented
  - Reserves resources for 60 seconds for claiming
  - Atomic multi-resource locking with rollback

- ❌ **Queue Strategy**: Priority + FIFO (matches LAVA/Slurm model)
  - ❌ Priority 1-10 (1 = highest) - not implemented
  - ✅ Currently: pure FIFO queue
  - ❌ Aging mechanism not implemented

- ✅ **Reservation Cleanup**:
  - Unclaimed fulfilled reservations expire after 60s
  - Background task removes expired/cancelled reservations
  - Atomic cleanup prevents race conditions

**Success Criteria:**
- ✅ Reservations automatically fulfilled when resources available
- ❌ WebSocket notifies clients in real-time (polling required currently)
- ❌ Higher priority reservations served first (no priority support yet)
- ✅ Reservations served FIFO (strict order by created_at)
- ✅ Abandoned reservations cleaned up automatically

---

## Phase 5 - Resource Maintenance & Unavailability (v0.5.0)

**Target:** Q1 2026

### Data Model Extensions
```python
class Resource(BaseModel):
    # ... existing fields ...
    unavailable: bool = False
    unavailable_reason: str | None = None  # e.g., "Hardware maintenance", "Network upgrade"
    unavailable_since: datetime | None = None
    unavailable_until: datetime | None = None  # Optional scheduled end time
```

### Core Features
- **Mark Resource Unavailable**: `POST /api/v1/resources/{id}/unavailable`
  ```json
  {
    "reason": "Hardware maintenance - replacing disk",
    "until": "2026-02-01T14:00:00Z"  // optional
  }
  ```
  - Requires maintainer/admin role (when auth implemented)
  - Prevents new locks and reservations
  - Does NOT unlock currently held locks (those expire normally)
  - Optional scheduled end time for automatic re-enablement

- **Mark Resource Available**: `POST /api/v1/resources/{id}/available`
  - Clears unavailable flag and reason
  - Resource becomes available for locking/reservations

- **Filter Unavailable Resources**:
  - `GET /api/v1/resources?available=true` - Show only available resources
  - `GET /api/v1/resources?unavailable=true` - Show only unavailable resources
  - Default behavior: show all resources with `unavailable` field

### Implementation Details
- ✅ Validation in lock endpoints: reject locks on unavailable resources
- ✅ Reservation matching: skip unavailable resources when fulfilling
- ❌ Background task: auto re-enable resources when `unavailable_until` passes
- ❌ Web UI: visual indicator for unavailable resources (gray out, badge)
- ✅ API response: include unavailability info in resource details

### Integration Points
- **With Locks**: Unavailable resources cannot be locked (409 Conflict)
- **With Reservations**: Unavailable resources excluded from matching pool
- **With Expiration**: Existing locks expire normally, resource stays unavailable
- **With Authentication** (Phase 6): Only admins/maintainers can toggle unavailability

### Use Cases
- CI infrastructure maintenance windows
- Hardware failures requiring repair
- Network upgrades or reconfiguration
- Resource decommissioning before removal
- Testing/debugging specific resources

**Success Criteria:**
- ❌ Resources can be marked unavailable with reason
- ❌ Unavailable resources rejected from lock operations
- ❌ Reservations skip unavailable resources
- ❌ Scheduled maintenance windows supported
- ❌ Web UI shows maintenance status clearly

---

## Phase 6 - Authentication & Audit Logging (v0.8.0)

**Target:** Mid Q2 2026

### Authentication
- **API Key Authentication**: Via `X-API-Key` header
  ```yaml
  # auth-config.yaml
  api_keys:
    - key: "abc123..."
      name: "Jenkins Production"
      role: "user"
    - key: "xyz789..."
      name: "Admin Console"
      role: "admin"
  ```

- **Role-Based Access Control**:
  - `admin` role: Full access (CRUD resources, view audit logs)
  - `user` role: Lock/unlock/reserve only (no resource creation)
  - `readonly` role: View-only access

- **JWT Support** (Optional): For advanced deployments
  - Token-based authentication
  - Configurable expiration
  - Claims-based authorization

### Audit Logging
```python
class AuditLog(BaseModel):
    timestamp: datetime
    event_type: str  # "lock", "unlock", "reserve", etc.
    resource_id: int | None
    client_id: str
    api_key_name: str
    success: bool
    details: dict
```

- Structured logging to separate file: `audit.jsonl`
- Queryable via API: `GET /api/v1/audit?from=...&to=...`
- Includes all resource state changes
- IP address and user agent tracking

### Implementation Details
- Add `--auth-config` flag to CLI
- Authentication middleware in FastAPI
- Graceful degradation (no auth = open access with warning)
- Rate limiting per API key (optional)

**Success Criteria:**
- Unauthorized requests return 401
- Role-based permissions enforced
- All operations logged with full context
- Audit logs include client identification

---

## Phase 7 - Persistence, Metrics & v1.0 Polish (v0.9.0 → v1.0.0)

**Target:** Late Q2 2026

### Persistence
- **SQLite Backend**: Optional via `--persist sqlite:///path/to/db.sqlite`
  - Tables: resources, locks, reservations, audit_log
  - Migrations using Alembic
  - Maintains in-memory as default (backward compatible)

- **State Recovery**: On startup
  - Reload resources from database
  - Restore active locks (with TTL validation)
  - Resume pending reservations

- **Migration Utilities**:
  - Import from YAML descriptor to database
  - Export database to YAML
  - Backup/restore commands

### Metrics
- **Prometheus Endpoint**: `GET /metrics`
  ```
  # Lock duration histogram
  rentabot_lock_duration_seconds_bucket{le="60"} 150

  # Active locks gauge
  rentabot_active_locks{tags="ci,linux"} 5

  # Queue depth gauge
  rentabot_reservation_queue_depth{priority="1"} 3

  # Resource utilization
  rentabot_resource_utilization_ratio 0.75
  ```

- **Metrics Tracked**:
  - Lock acquisition rate
  - Lock duration percentiles (p50, p95, p99)
  - Queue wait time
  - Resource utilization by tags
  - API request rate and latency

### API Enhancements
- **Pagination**: `GET /api/v1/resources?page=1&limit=50`
- **Filtering**: `GET /api/v1/resources?locked=true&tags=ci,linux`
- **Sorting**: `GET /api/v1/resources?sort=name&order=asc`
- **Partial Updates**: `PATCH /api/v1/resources/{id}` for metadata

### Documentation & Polish
- Comprehensive OpenAPI docs with examples
- API versioning strategy documented
- Deprecation policy (12 months notice for breaking changes)
- Docker image published to Docker Hub
- Kubernetes deployment manifests (Deployment, Service, Ingress)
- Helm chart for easy installation

### Performance
- Benchmark tests (1000+ resources, 100+ concurrent locks)
- Memory profiling and optimization
- Connection pooling for database
- Caching for frequently accessed resources

**Success Criteria:**
- Database persistence fully functional
- Prometheus metrics integration tested
- API supports pagination and filtering
- Docker deployment verified
- Performance benchmarks documented
- v1.0.0 release candidate tested in production-like environment

---

## v1.0.0 Release Criteria

### Feature Completeness
- ✅ Basic resource CRUD
- ✅ Lock/unlock with tokens
- ✅ N-of-M allocation
- ✅ Lock TTL and auto-expiration
- ✅ Reservation queue with priority
- ✅ Authentication and RBAC
- ✅ Audit logging
- ✅ Optional persistence
- ✅ Prometheus metrics

### Production Readiness
- ✅ Health check endpoints
- ✅ Comprehensive error handling
- ✅ Structured logging
- ✅ API documentation (OpenAPI)
- ✅ Container deployment (Docker)
- ✅ Orchestration support (Kubernetes/Helm)
- ✅ Performance benchmarks
- ✅ Security best practices

### Quality Assurance
- ✅ >90% test coverage
- ✅ Integration tests for all workflows
- ✅ Load testing (sustained 100 req/s)
- ✅ Security audit (dependency scanning)
- ✅ Documentation review
- ✅ Migration guide from v0.x

### Community
- ✅ Installation guide
- ✅ Quick start tutorial
- ✅ API client examples (Python, curl, Jenkins)
- ✅ Troubleshooting guide
- ✅ Contributing guidelines
- ✅ Changelog following Keep a Changelog format

---

## Post-1.0 Future Considerations

### Advanced Features (v1.x)
- Label expressions (complex tag matching with AND/OR/NOT)
- Resource quantities (pool of N identical resources)
- Maintenance windows (scheduled resource unavailability)
- Resource health checks (periodic validation)
- Multi-tenancy (namespace isolation)

### Scalability (v2.0)
- Distributed deployment (Redis or etcd backend)
- Horizontal scaling (multiple instances)
- Event streaming (Kafka/RabbitMQ integration)
- GraphQL API alongside REST

### Integrations
- Jenkins Pipeline library
- GitHub Actions workflow
- GitLab CI/CD integration
- Ansible module
- Terraform provider
- Resource maintenance hooks (notify on unavailability)

---

## Decision Log

### Tag Separator: Space → Comma
**Decision**: Migrate to comma-separated tags
**Rationale**: Better querystring compatibility, maps directly to JSON arrays, industry standard
**Timeline**: v0.4.0 with backward-compatible parser

### API Path Simplification
**Decision**: `/api/v1/` instead of `/rentabot/api/v1.0/`
**Rationale**: Shorter, more conventional, easier to type
**Timeline**: v0.4.0 with redirect from old paths

### Queue Priority Strategy
**Decision**: Priority levels (1-10) with FIFO within priority
**Rationale**: Matches industry standards (LAVA, Slurm), balances flexibility and simplicity
**Timeline**: v0.7.0

### Persistence Default
**Decision**: In-memory default, optional SQLite
**Rationale**: Maintains simplicity for development/testing, allows production persistence
**Timeline**: v0.9.0

### Authentication Approach
**Decision**: API key primary, JWT optional
**Rationale**: API keys simpler for automation, JWT for browser/advanced scenarios
**Timeline**: v0.8.0

---

## Version Numbering

Following Semantic Versioning (SemVer 2.0):
- **Major (v1.0)**: Breaking changes, API incompatibility
- **Minor (v1.1)**: New features, backward compatible
- **Patch (v1.0.1)**: Bug fixes, no new features

Pre-1.0 versions (v0.x) may include breaking changes in minor versions.

---

## Contributing to This Roadmap

This roadmap is a living document. Feedback welcome via GitHub issues:
- Feature requests: Tag with `enhancement`
- Priority disputes: Tag with `roadmap-discussion`
- Timeline concerns: Tag with `planning`

Last Updated: 28 January 2026
