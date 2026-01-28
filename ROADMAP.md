# Development Roadmap - Post v1.0.0

## High-Level Goals

**rentabot** is a resource locking service designed to coordinate shared resource access across CI/CD pipelines and automated systems. The v1.0.0 release established the core foundation. Future development focuses on three key pillars:

1. **Operational Visibility**: Enhanced tracking, monitoring, and observability for production deployments
2. **User Experience**: Improved web UI with real-time updates and better resource management controls
3. **Production Readiness**: Authentication, persistence, and enterprise-grade reliability features

The roadmap prioritizes practical features that solve real-world coordination challenges in automated environments.

---

## What's Complete (v1.0.0 - January 2026)

✅ **Core Resource Management**
- Lock/unlock with TTL and automatic expiration
- Multi-resource atomic locking via reservations
- FIFO reservation queue with 60s claim window
- Health check endpoints (`/health`, `/readiness`)
- Comma-separated tag format
- Simplified `/api/v1/` API paths

## What's Next

The following features are planned for upcoming releases. This roadmap focuses on production readiness and operational improvements.

---

## v1.1.0 - Lock Tracking & Frontend Improvements

**Target:** February 2026

### Lock Tracking & Metadata
- **"Locked By" Information**:
  ```python
  class Resource(BaseModel):
      # ... existing fields ...
      locked_by_label: str | None = None  # e.g., "jenkins-job-123", "user@example.com"
      locked_by_ip: str | None = None     # IP address of lock requester
  ```
  - Track who/what locked the resource (human-readable label)
  - Record IP address of lock operation
  - Display in API responses and web UI
  - Clear on unlock

### Frontend Enhancements
- **Auto-Refresh**:
  - Automatic page refresh every 10-30 seconds
  - Optional: WebSocket for real-time updates
  - Visual indicator showing last refresh time

- **TTL Display**:
  - Show remaining lock time for each locked resource
  - Countdown timer (e.g., "15:30 remaining")
  - Warning indicator when < 5 minutes remain
  - Color coding: green > 15min, yellow 5-15min, red < 5min

- **Reservation Queue Display**:
  - New section showing active reservations
  - Columns: ID, Tags, Quantity, Status, Position, Created
  - Real-time status updates (pending → fulfilled → claimed)

- **Improved Status Labels**:
  - Current: "Resource is available", "Resource is locked"
  - New: Single-word status badges
    - `Available` (green)
    - `Locked` (red)
    - `Unavailable` (gray)
    - `Reserved` (yellow)

- **Table Sorting & Filtering**:
  - Sortable columns (name, status, tags, lock time)
  - Filter by status: All / Available / Locked / Unavailable
  - Filter by tags
  - Search by name or description

### Admin Controls (Frontend)
- **Resource Management Buttons**:
  - "Mark Unavailable" button for admins
  - Modal dialog for unavailability reason
  - Optional scheduled re-enablement time
  - "Mark Available" button to re-enable
  - Requires admin authentication

**API Changes:**
- Add `locked_by_label` and `locked_by_ip` to lock endpoint requests
- Capture IP from `request.client.host` in FastAPI

**API Changes:**
- Add `locked_by_label` and `locked_by_ip` to lock endpoint requests
- Capture IP from `request.client.host` in FastAPI

---

## v1.2.0 - Resource Maintenance & Unavailability

**Target:** March 2026

### Mark Resources Unavailable
- **Data Model**:
  ```python
  class Resource(BaseModel):
      # ... existing fields ...
      unavailable: bool = False
      unavailable_reason: str | None = None
      unavailable_since: datetime | None = None
      unavailable_until: datetime | None = None  # Optional scheduled end
  ```

- **API Endpoints**:
  - `POST /api/v1/resources/{id}/unavailable` - Mark unavailable (admin only)
  - `POST /api/v1/resources/{id}/available` - Re-enable (admin only)
  - `GET /api/v1/resources?available=true` - Filter available only

- **Behavior**:
  - Prevents new locks (409 Conflict)
  - Excluded from reservation matching
  - Existing locks expire normally
  - Optional auto re-enablement at `unavailable_until`

- **Frontend**:
  - Visual indicator (grayed out, "Unavailable" badge)
  - Display reason in tooltip
  - Admin controls integrated

**Use Cases:** Hardware maintenance, network upgrades, failures, decommissioning

---

## v1.3.0 - Simplified Authentication

**Target:** April 2026

### Two-Role Authentication Model

**Simplified Approach** (to be discussed):
- **Admin Token**: Defined in configuration file
  - Full access to all operations
  - Can mark resources unavailable
  - Can force unlock resources
  - Overrides all other tokens

- **User Tokens**: Regular API access
  - Can lock/unlock/reserve resources
  - Cannot modify resource state (unavailable)
  - Cannot force unlock others' locks

### Configuration
```yaml
# auth-config.yaml
auth:
  admin_token: "admin-secret-token-xyz"  # Single admin token
  enabled: true  # Set to false to disable auth (default: false)

# Optional: user tokens for access control
user_tokens:
  - "user-token-abc-jenkins"
  - "user-token-def-github"
```

### Implementation
- Simple token check via `X-API-Key` header
- Admin token has full privileges
- User tokens have standard access
- No auth = open access (with warning log)
- Token validation middleware in FastAPI

### Lock Tracking Integration
- Record token name/type in lock metadata
- Track which token locked which resource
- Audit log: token, IP address, operation, timestamp

**Note:** Role-based complexity (maintainer, readonly) deferred. Focus on simple admin/user split.

**Note:** Role-based complexity (maintainer, readonly) deferred. Focus on simple admin/user split.

---

## v1.4.0 - Persistence & State Recovery

**Target:** May 2026

### SQLite Backend (Optional)
- **Configuration**: `--persist sqlite:///path/to/rentabot.db`
- **Tables**: resources, locks, reservations, audit_log
- **Default**: In-memory (current behavior)
- **State Recovery**: Reload resources, restore active locks on startup
- **Migrations**: Using Alembic for schema management

### Features
- Import/export YAML ↔ SQLite
- Backup/restore commands
- Lock validation on recovery (check TTL expiration)
- Resume pending reservations

---

## v1.5.0 - Monitoring & Metrics

**Target:** June 2026

### Prometheus Metrics
- **Endpoint**: `GET /metrics`
- **Metrics**:
  - Active locks gauge by tags
  - Lock duration histogram
  - Reservation queue depth
  - Resource utilization ratio
  - Lock expiration rate
  - API request rate and latency

### API Enhancements
- Pagination: `?page=1&limit=50`
- Advanced filtering: `?locked=true&tags=ci,linux&unavailable=false`
- Sorting: `?sort=name&order=asc`
- Expired locks endpoint: `GET /api/v1/resources/expired`

---

## Future Considerations (v1.6+)

### Pending from Earlier Phases
- ❌ Batch unlock endpoint
- ❌ Priority-based reservation queue (currently FIFO only)
- ❌ WebSocket notifications for reservations
- ❌ Quantity parameter on direct lock endpoints

### Advanced Features
- Docker image and Kubernetes manifests
- Prometheus alerting rules
- Resource health checks
- Multi-resource group locking (named groups)
- Scheduled maintenance windows

### Integrations
- Jenkins Pipeline library
- GitHub Actions workflow
- GitLab CI/CD integration
- Webhook notifications

---

## Decision Log

### Authentication Simplification
**Decision**: Two-role model (admin + users) instead of complex RBAC
**Rationale**: Simpler to implement and maintain, covers 95% of use cases
**Status**: To be discussed and finalized

### Frontend Priority
**Decision**: Focus on usability improvements before advanced features
**Rationale**: Better UX improves adoption, real-time updates are critical
**Target**: v1.1.0

### Persistence Timing
**Decision**: Defer to v1.4.0 (after auth and frontend)
**Rationale**: In-memory sufficient for current use cases, focus on features first
**Rationale**: In-memory sufficient for current use cases, focus on features first

---

## Contributing to This Roadmap

This roadmap is a living document. Priorities may shift based on:
- User feedback and feature requests
- Production deployment needs
- Security or performance issues

Feedback welcome via GitHub issues with tags:
- `enhancement` - Feature requests
- `roadmap-discussion` - Priority or timeline concerns

---

**Last Updated:** 31 January 2026
**Current Version:** v1.0.0
**Next Release:** v1.1.0 (February 2026)

Last Updated: 28 January 2026
