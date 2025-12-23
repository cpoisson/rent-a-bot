# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Logging uses standard logging module instead of daiquiri.

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
- Migrated from Flask to FastAPIpypi-AgEIcHlwaS5vcmcCJDlmYjllYjU4LTQ1NzUtNDFmMS05NTE0LWUzZDk5NDIwYTIyMQACElsxLFsicmVudC1hLWJvdCJdXQACLFsyLFsiNDVhZTgxMmUtMzA2OC00OTRiLWE3MDMtNWE1YWM4NDE0ODAzIl1dAAAGILtLZeOe9MAeOwT5GHCX8DfHYAUlcCaXVekr3P8om4Gq
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
