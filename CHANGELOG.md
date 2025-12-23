# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- CLI support
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
