# augeo-platform Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-25

## Active Technologies
- Python 3.11+ (Backend), TypeScript (Frontend) + FastAPI, SQLAlchemy, Pydantic, React, Zustand
- Authentication: OAuth2 + JWT, bcrypt password hashing, Redis sessions (001-user-authentication-role)
- Monitoring: Prometheus metrics, structured logging, health checks (001-user-authentication-role)

## Project Structure
```
src/
tests/
```

## Commands

### Backend (Python)
**CRITICAL**: Always use Poetry for Python commands. Never use pip, venv, or virtualenv directly.

- Run tests: `cd backend && poetry run pytest`
- Run linter: `cd backend && poetry run ruff check .`
- Run formatter: `cd backend && poetry run black .`
- Install dependencies: `cd backend && poetry install`
- Add package: `cd backend && poetry add <package>`
- Run any Python command: `cd backend && poetry run <command>`

### Frontend
- Install: `pnpm install`
- Dev server: `pnpm dev`
- Build: `pnpm build`
- Test: `pnpm test`

## Development Environment

### Python Environment
- **Package Manager**: Poetry (ALWAYS use `poetry run` for all Python commands)
- **Virtual Environment**: Managed by Poetry at `~/.cache/pypoetry/virtualenvs/`
- **Never use**: pip install, venv/bin/activate, python -m commands directly
- **Always use**: `poetry run python`, `poetry run pytest`, etc.

## Code Style
Python 3.11+ (Backend), TypeScript (Frontend): Follow standard conventions

## Git Workflow

### Committing Changes
**CRITICAL**: Always run pre-commit hooks before committing to ensure code quality.

**Recommended workflow**:
```bash
./scripts/safe-commit.sh      # Run pre-commit hooks with auto-retry
git commit -m "your message"  # Commit when hooks pass
```

**Why use safe-commit.sh**: The script:
- Runs pre-commit hooks to completion
- Auto-stages formatting changes (ruff, black, trailing whitespace, etc.)
- Re-runs hooks after auto-fixes to verify (up to 3 attempts)
- Exits successfully when all checks pass
- Prevents committing code that fails linting/formatting

**Manual pre-commit workflow** (if not using safe-commit.sh):
```bash
git add -A
pre-commit run --all-files
# If changes were made, re-stage and re-run:
git add -A
pre-commit run --all-files
# Then commit:
git commit -m "message"
```

## Recent Changes
- 001-user-authentication-role: Completed Phase 12 Polish (T154-T161, T165, T167)
  - ✅ OpenAPI documentation enhanced with contact, license, and tags
  - ✅ Comprehensive health checks: /health, /health/detailed, /health/ready, /health/live
  - ✅ Prometheus metrics: /metrics endpoint with HTTP counters, failure tracking, up/down gauge
  - ✅ Error handling: Database, Redis, and email retry logic with exponential backoff
  - ✅ Request ID tracing: X-Request-ID header for distributed tracing
  - ✅ CORS configuration for cross-origin requests
  - ✅ Backend and frontend READMEs updated with complete setup instructions
- 002-npo-creation: Added Python 3.11+ (Backend), TypeScript (Frontend) + FastAPI, SQLAlchemy, Pydantic, React, Zustand

## API Endpoints (001-user-authentication-role)

### Authentication
- `POST /api/v1/auth/register` - Register new user (with email verification)
- `POST /api/v1/auth/login` - Login (rate-limited: 5 attempts/15min)
- `POST /api/v1/auth/logout` - Logout and revoke session
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/verify-email` - Verify email address
- `POST /api/v1/auth/verify-email/resend` - Resend verification email

### Password Management
- `POST /api/v1/auth/password/reset/request` - Request password reset
- `POST /api/v1/auth/password/reset/confirm` - Confirm password reset with token
- `POST /api/v1/auth/password/change` - Change password (authenticated)

### User Management (Admin only)
- `GET /api/v1/users` - List users with pagination/filtering
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user details
- `PATCH /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Soft delete user
- `PATCH /api/v1/users/{id}/role` - Update user role
- `POST /api/v1/users/{id}/activate` - Reactivate user

### Health & Monitoring
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed service status (DB, Redis, email)
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe
- `GET /metrics` - Prometheus metrics

## Authentication & Authorization

### Session Management
- Access tokens: 15-minute expiry (JWT)
- Refresh tokens: 7-day expiry (stored in Redis)
- Session tracking: Device info (user-agent, IP) stored in PostgreSQL
- Automatic token refresh: Frontend axios interceptor handles 401s
- Session expiration warning: Modal appears 2 minutes before expiry

### Role-Based Access Control
- **Roles**: Super Admin, NPO Admin, NPO Staff, Check-in Staff, Donor
- **Permission Service**: Centralized authorization logic in `PermissionService`
- **Middleware**: `@require_role()` and `@require_permission()` decorators
- **Audit Logging**: All auth events tracked in `audit_logs` table

### Rate Limiting
- Login endpoint: 5 attempts per 15 minutes (per IP)
- Password reset: 3 attempts per hour
- Redis-backed with sorted sets for distributed rate limiting
- Custom decorator: `@rate_limit()` in `app/middleware/rate_limit.py`

## Monitoring & Observability

### Metrics (Prometheus)
- `augeo_http_requests_total` - HTTP requests by method/path/status
- `augeo_db_failures_total` - Database connection failures
- `augeo_redis_failures_total` - Redis connection failures
- `augeo_email_failures_total` - Email send failures
- `augeo_up` - Application up/down status (1=up, 0=down)

### Structured Logging
- JSON format with request IDs for distributed tracing
- X-Request-ID header in all responses
- Context propagation via ContextVar
- Log levels: DEBUG, INFO, WARNING, ERROR

### Health Checks
- Basic: Quick liveness check
- Detailed: DB ping, Redis ping, email config validation
- Ready: Kubernetes readiness probe
- Live: Kubernetes liveness probe

## Testing (001-user-authentication-role)
- **224 tests** with 40% coverage
- Contract tests: API endpoint validation
- Integration tests: Full auth flows (login, registration, password reset, token refresh)
- Unit tests: Security, permissions, password hashing, JWT blacklist
- Test fixtures: Authenticated clients, test users with different roles
- Coverage: `poetry run pytest --cov=app --cov-report=html`

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
