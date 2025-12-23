# Rent-A-Bot Improvement Plan

Generated: 23 December 2025

## 🎯 Architecture & Design

### 1. Simplify the Data Model
**Issue:** Dual indexing (`resources_by_id` and `resources_by_name`) creates maintenance overhead and sync risks.
- **Current Location:** `rentabot/models.py` lines 38-40
- **Solution:** Use a single dictionary with ID as key, add helper methods for name/tag lookups
- **Benefit:** Reduces code complexity, eliminates sync issues
- **Priority:** Medium

### 2. Replace Threading Lock with AsyncIO
**Issue:** Using `threading.Lock` in an async FastAPI app is a mismatch
- **Current Location:** `rentabot/controllers.py` line 22
- **Solution:** Use `asyncio.Lock()` and make controller functions async
- **Benefit:** Better performance, proper async/await patterns
- **Priority:** High

### 3. Inconsistent Naming
**Issues:**
- Typo: `get_all_ressources()` should be `get_all_resources()` (controllers.py line 29)
- Mixed conventions: `lock_by_criterias` vs `lock_by_id`
- **Solution:** Standardize all naming to English spelling and consistent conventions
- **Priority:** High

## 🔧 Code Quality Issues

### 4. Remove Custom `.dict` Property
**Issue:** Pydantic v2 uses `model_dump()`, the custom `.dict` property is redundant
- **Current Location:** `rentabot/models.py` lines 24-35`
- **Solution:** Use built-in `model_dump(by_alias=True)`
- **Benefit:** Standard Pydantic patterns, less custom code
- **Priority:** Medium

### 5. Simplify Exception Handlers
**Issue:** Separate handler for each exception type is verbose
- **Current Location:** `rentabot/main.py` lines 165-191
- **Solution:** Single handler for `ResourceException` base class
- **Benefit:** DRY principle, easier maintenance
- **Priority:** High

### 6. Improve Error Response Structure
**Issue:** Inconsistent error payloads
- **Solution:** Standardize on FastAPI's HTTPException or Problem Details (RFC 7807)
- **Benefit:** Better API consistency, standard error format
- **Priority:** Medium

## 🚀 Functionality Improvements

### 7. Add Resource Persistence
**Issue:** In-memory storage loses all data on restart
- **Solution:** Add optional persistence with SQLite or JSON file
- **Benefit:** Production-ready, survives restarts
- **Priority:** Low

### 8. Add Lock Expiration/Timeout
**Issue:** Locks never expire if client crashes
- **Solution:** Add optional TTL for locks with background cleanup task
- **Benefit:** Prevents resource deadlocks
- **Priority:** Medium

### 9. Health Check Endpoint
**Missing:** `/health` or `/readiness` endpoints
- **Solution:** Add basic health endpoints for monitoring
- **Benefit:** Better observability in production
- **Priority:** High

### 10. API Versioning Cleanup
**Issue:** Verbose URL paths (`/rentabot/api/v1.0/`)
- **Solution:** Simplify to `/api/v1/` or use API router prefix
- **Benefit:** Cleaner URLs, easier to read
- **Priority:** Low

## 📝 Configuration & Dependencies

### 11. Outdated Python Support
**Issue:** Claims Python 3.7+ support but uses modern syntax
- **Current:** `dict[int, Resource]` syntax requires Python 3.9+ (models.py line 38)
- **Location:** `pyproject.toml` line 28
- **Solution:** Update `requires-python = ">=3.9"` in pyproject.toml
- **Benefit:** Honest requirements, avoids confusion
- **Priority:** High

### 12. Missing Type Hints
**Issue:** Some functions lack type hints (controllers)
- **Solution:** Add complete type hints throughout
- **Benefit:** Better IDE support, catch bugs earlier
- **Priority:** Medium

## 🧪 Testing & Documentation

### 13. OpenAPI Schema Enhancement
- Add more examples to response models
- Add request body schemas for lock/unlock
- Document error responses
- **Priority:** Low

### 14. Add Metrics/Logging
- Track lock/unlock operations
- Add structured logging
- Consider adding Prometheus metrics
- **Priority:** Low

## 📊 Implementation Priority

### High Priority (Quick Wins)
1. ⬜ Fix typo: `ressources` → `resources`
2. ✅ Replace `threading.Lock` with `asyncio.Lock` - **COMPLETED 2025-12-23**
3. ⬜ Fix Python version in pyproject.toml
4. ⬜ Consolidate exception handlers
5. ⬜ Add health check endpoint

### Medium Priority
6. ⬜ Replace custom `.dict` with `model_dump()`
7. ⬜ Add lock expiration/TTL
8. ⬜ Simplify API URL paths
9. ⬜ Add complete type hints
10. ⬜ Simplify data model (single dictionary)

### Low Priority (Nice to Have)
11. ⬜ Add persistence option
12. ⬜ Add metrics/monitoring
13. ⬜ Enhanced OpenAPI documentation
14. ⬜ API versioning cleanup

## 📝 Notes

- Review each change before implementation
- Ensure all tests pass after each modification
- Update documentation as changes are made
- Consider backward compatibility for API changes
