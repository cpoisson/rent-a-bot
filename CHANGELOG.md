# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed
- **BREAKING**: Removed legacy `/rentabot/api/v1.0/` API endpoints - use `/api/v1/` instead
- Removed legacy API deprecation middleware and redirect functionality
- Removed `RENTABOT_LEGACY_REDIRECT` environment variable support

### Added
- Simplified API endpoints under `/api/v1/` path (new standard)
- Pre-commit hook for automatic code formatting and linting with ruff
- `/health` endpoint for basic service monitoring and uptime checks
- `/readiness` endpoint for Kubernetes readiness probes
- **Lock timeout/TTL feature with automatic expiration**:
  - `ttl` parameter on lock endpoints (default: 3600s = 1 hour)
  - Automatic background task to expire locks after TTL
  - `lock_acquired_at`, `lock_expires_at`, and `max_lock_duration` fields on resources
  - Maximum lock duration enforcement (default: 24 hours per resource)
  - `POST /api/v1/resources/{id}/extend` endpoint to extend lock duration
  - Lock extension with validation against max_lock_duration
  - ISO 8601 timestamp serialization for all datetime fields
- **Smart reservation queue feature (FIFO)**:
  - `POST /api/v1/reservations` endpoint to create reservations for unavailable resources
  - `GET /api/v1/reservations/{id}` endpoint to check reservation status
  - `POST /api/v1/reservations/{id}/claim` endpoint to claim fulfilled reservations
  - `DELETE /api/v1/reservations/{id}` endpoint to cancel pending reservations
  - `GET /api/v1/reservations` endpoint to list all active reservations
  - Automatic background task to fulfill pending reservations in FIFO order
  - 60-second claim window for fulfilled reservations
  - Automatic cleanup of expired pending and unclaimed reservations
  - Multi-resource locking with atomic rollback on failure
  - Queue position tracking for pending reservations
  - Support for custom `max_wait_time` and `ttl` parameters

### Changed
- **BREAKING**: Tag format changed from space-separated to comma-separated (e.g., `"tag1,tag2,tag3"` instead of `"tag1 tag2 tag3"`)
- **BREAKING**: Minimum Python version requirement updated to 3.10 (from 3.9, which reached EOL in October 31st 2025)
- Consolidated duplicate exception handlers into single handler following DRY principles
- Replaced custom `.dict` property with standard `to_dict()` method in exception classes
- Logging uses standard logging module instead of daiquiri.
- Replaced `threading.Lock` with `asyncio.Lock` for better async compatibility.
- Fixed typo in `get_all_resources` function name.
- Removed dual indexing of resources; now using a single dictionary with ID as key.
- API documentation and examples updated to use `/api/v1/` paths
- README standardized to port 8000 and corrected query parameter examples
- Lock and unlock endpoints now clear/set timestamp fields appropriately
- All resource serialization uses `mode='json'` for proper datetime handling

### Fixed
- Early TTL validation in `create_reservation()` to prevent impossible-to-fulfill reservations
  - Now validates that sufficient resources can accommodate requested TTL before creating reservation
  - Provides clear error message when TTL exceeds `max_lock_duration` for available resources
  - Prevents reservations from staying "pending" indefinitely due to TTL constraints

### Deprecated
- Legacy `/rentabot/api/v1.0/` endpoints (will be removed in v1.0.0)

---

## [0.3.0] - 2025-12-23
### Added
- CLI tool for easy server startup (`rentabot` command)
- Automatic configuration file discovery (current dir, home dir, environment variable)
- CLI options: `--config`, `--host`, `--port`, `--reload`, `--log-level`
- Support for `.rentabot.yaml` and `rentabot.yaml` config files
- Dynamic version reading from package metadata
- Code quality tooling with ruff (formatting and linting)

### Changed
- Package name from `rent-a-bot` to `rentabot` for consistency
- Improved test coverage to near 100%

### Fixed
- Unbound variable issue in `get_an_available_resource` when all tagged resources are locked
- Edge cases in resource locking logic

---

## [0.2.0] - 2025-12-22
### Changed
- Migrated from Flask to FastAPI
- Replaced SQLAlchemy with Pydantic models and in-memory storage
- Modernized packaging to use pyproject.toml exclusively

### Removed
- SQLite database dependency
- Legacy setup.py, setup.cfg, and MANIFEST.in files

---

## [0.1.0] - 2017-12-09
### Added
- Restful API to retrieve an available resource using an id, a name, or tags as an input. (/rentabot/api/v1.0/resources/lock)

---

## [0.0.6] - 2017-11-26
### Added
- Logs using daiquiri

---

## [0.0.5] - 2017-11-18
### Changed
- Refactor view and controllers to isolate db transactions into the controller.

---

## [0.0.4] - 2017-10-24
### Fixed
- Fix a potential race condition on a multi threaded server context [Issues-2](https://github.com/cpoisson/rent-a-bot/issues/2)

---

## [0.0.1] - 2017-10-19
### Added
- Basic project setup (readme, changelog, CI, gitignore...)
- Flask application first layout
- Functional tests
- Resource Model and GET REST api
- Resource Lock and Unlock API
- A (very) basic front end to display resources
- Resource descriptor yaml file handling at startup
