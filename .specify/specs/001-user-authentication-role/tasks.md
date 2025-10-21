# Tasks: User Authentication & Role Management

**Input**: Design documents from `.specify/specs/001-user-authentication-role/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are included as this is a security-critical feature requiring comprehensive validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions
Based on plan.md: Web application structure with `backend/` and `frontend/` directories.

---

## Phase 1: Setup (Shared Infrastructure) ✅ COMPLETE

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend directory structure per plan.md: backend/app/{models,schemas,services,api,middleware,core,tests}
- [x] T002 Initialize Poetry project with pyproject.toml in backend/ with dependencies: fastapi>=0.104.0, sqlalchemy>=2.0.0, pydantic>=2.0.0, python-jose[cryptography], passlib[bcrypt], alembic, redis, pytest, factory-boy
- [x] T003 [P] Configure pre-commit hooks with ruff (linting), black (formatting), mypy (type checking) in .pre-commit-config.yaml
- [x] T004 [P] Create backend/.env.example with environment variables from quickstart.md
- [x] T005 [P] Create docker-compose.yml for PostgreSQL 15 and Redis 7 per quickstart.md
- [x] T006 [P] Create backend/alembic.ini and backend/alembic/env.py for database migrations
- [x] T007 [P] Setup pytest configuration in backend/pytest.ini with coverage reporting
- [x] T008 [P] Create GitHub Actions workflow .github/workflows/backend-ci.yml for lint/test/type-check
- [x] T009 [P] Initialize frontend/augeo-admin with Vite + React 18 + TypeScript 5
- [x] T010 [P] Setup frontend dependencies: zustand, react-query, react-router-dom, axios in frontend/augeo-admin/package.json
- [x] T011 [P] Create shared TypeScript types in frontend/shared/types/{user.ts, auth.ts, role.ts}

**Completed**: October 20, 2025 | **PR**: #1 Setup

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T012 Create database.py with SQLAlchemy async engine configuration in backend/app/core/database.py
- [x] T013 [P] Create Redis client configuration with connection pooling in backend/app/core/redis.py
- [x] T014 [P] Create Base model with UUID primary key and timestamps in backend/app/models/base.py
- [x] T015 [P] Create config.py with Settings class (Pydantic BaseSettings) in backend/app/core/config.py
- [x] T016 [P] Create security.py with bcrypt context and JWT utilities in backend/app/core/security.py
- [x] T017 [P] Create error handlers for HTTPException, ValidationError in backend/app/core/errors.py
- [x] T018 [P] Create logging configuration with structured JSON logging in backend/app/core/logging.py
- [x] T019 [P] Create Alembic migration 001_create_roles_table.py with Role model and seed 5 roles per data-model.md
- [x] T020 Create API router structure in backend/app/api/v1/{auth.py, users.py, __init__.py}
- [x] T021 Create FastAPI app instance with CORS, middleware, and exception handlers in backend/app/main.py
- [x] T022 [P] Create test fixtures for database, Redis, and test client in backend/app/tests/conftest.py

**Completed**: October 20, 2025 | **PR**: #2 Foundational Infrastructure

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - User Registration & Login (Priority: P1) 🎯 MVP

**Goal**: New users can create accounts and existing users can securely access the system with their credentials.

**Independent Test**: Create a new account, logout, and log back in. Verify JWT tokens are issued and validated.

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T023 [P] [US1] Create contract test for POST /api/v1/auth/register in backend/app/tests/contract/test_auth_register.py
- [x] T024 [P] [US1] Create contract test for POST /api/v1/auth/login in backend/app/tests/contract/test_auth_login.py
- [x] T025 [P] [US1] Create contract test for POST /api/v1/auth/logout in backend/app/tests/contract/test_auth_logout.py
- [x] T026 [P] [US1] Create integration test for registration → login flow in backend/app/tests/integration/test_auth_flow.py
- [x] T027 [P] [US1] Create unit test for JWT token creation/verification in backend/app/tests/unit/test_security.py
- [x] T028 [P] [US1] Create unit test for password hashing in backend/app/tests/unit/test_password.py

### Implementation for User Story 1

- [x] T029 [P] [US1] Create User model with SQLAlchemy per data-model.md in backend/app/models/user.py
- [x] T030 [P] [US1] Create Alembic migration 002_create_users_table.py with indexes and constraints
- [x] T031 [P] [US1] Create Session model (PostgreSQL audit) in backend/app/models/session.py
- [x] T032 [P] [US1] Create Alembic migration 003_create_sessions_table.py (migration 003, not 004 - permissions table deferred)
- [x] T033 [P] [US1] Create Pydantic schemas: UserCreate, UserPublic, LoginRequest, LoginResponse in backend/app/schemas/auth.py
- [x] T034 [US1] Implement AuthService with register(), login(), logout() methods in backend/app/services/auth_service.py
- [x] T035 [US1] Implement SessionService with create_session(), revoke_session() methods in backend/app/services/session_service.py
- [x] T036 [US1] Implement JWT token utilities: create_access_token(), create_refresh_token(), verify_token() in backend/app/core/security.py
- [x] T037 [US1] Implement Redis session storage: set_session(), get_session(), delete_session() in backend/app/services/redis_service.py
- [x] T038 [US1] Implement POST /api/v1/auth/register endpoint per contracts/auth.yaml in backend/app/api/v1/auth.py
- [x] T039 [US1] Implement POST /api/v1/auth/login endpoint with rate limiting per contracts/auth.yaml in backend/app/api/v1/auth.py
- [x] T040 [US1] Implement POST /api/v1/auth/logout endpoint per contracts/auth.yaml in backend/app/api/v1/auth.py
- [ ] T041 [US1] Create authentication middleware to extract/validate JWT from Authorization header in backend/app/middleware/auth.py
- [ ] T042 [US1] Add validation: email uniqueness check, password strength (8+ chars, 1 letter, 1 number) in backend/app/schemas/auth.py
- [ ] T043 [US1] Add audit logging for login, logout, failed_login events in backend/app/services/audit_service.py
- [ ] T044 [US1] Implement rate limiting for login endpoint (5 attempts/15min) using Redis sorted sets in backend/app/middleware/rate_limit.py
- [ ] T045 [P] [US1] Create login form component in frontend/augeo-admin/src/features/auth/LoginForm.tsx
- [ ] T046 [P] [US1] Create registration form component in frontend/augeo-admin/src/features/auth/RegisterForm.tsx
- [ ] T047 [US1] Create auth store with Zustand: login(), logout(), getUser() in frontend/augeo-admin/src/stores/auth-store.ts
- [ ] T048 [US1] Create axios interceptor for adding Authorization header in frontend/augeo-admin/src/lib/axios.ts
- [ ] T049 [US1] Create ProtectedRoute component that checks auth state in frontend/augeo-admin/src/components/ProtectedRoute.tsx
- [ ] T050 [US1] Add login/register routes to React Router in frontend/augeo-admin/src/routes/__root.tsx

**Checkpoint**: At this point, User Story 1 should be fully functional - users can register, login, and logout with JWT tokens

---

## Phase 4: User Story 2 - Password Recovery & Security (Priority: P2)

**Goal**: Users can recover access to their accounts when they forget their passwords and manage their account security settings.

**Independent Test**: Initiate password reset flow, receive reset email (check Redis for token in dev), and successfully change password to regain access.

### Tests for User Story 2

- [ ] T051 [P] [US2] Create contract test for POST /api/v1/password/reset/request in backend/app/tests/contract/test_password_reset.py
- [ ] T052 [P] [US2] Create contract test for POST /api/v1/password/reset/confirm in backend/app/tests/contract/test_password_reset.py
- [ ] T053 [P] [US2] Create contract test for POST /api/v1/password/change in backend/app/tests/contract/test_password_change.py
- [ ] T054 [P] [US2] Create integration test for password reset flow in backend/app/tests/integration/test_password_reset_flow.py
- [ ] T055 [P] [US2] Create unit test for password reset token generation/validation in backend/app/tests/unit/test_password_tokens.py

### Implementation for User Story 2

- [ ] T056 [P] [US2] Create Pydantic schemas: PasswordResetRequest, PasswordResetConfirm, PasswordChangeRequest in backend/app/schemas/password.py
- [ ] T057 [US2] Implement Azure Communication Services email client in backend/app/services/email_service.py
- [ ] T058 [US2] Implement PasswordService with request_reset(), confirm_reset(), change_password() methods in backend/app/services/password_service.py
- [ ] T059 [US2] Implement password reset token utilities: generate_token(), store_token(), validate_token() using Redis in backend/app/services/redis_service.py
- [ ] T060 [US2] Implement POST /api/v1/password/reset/request endpoint per contracts/auth.yaml in backend/app/api/v1/auth.py
- [ ] T061 [US2] Implement POST /api/v1/password/reset/confirm endpoint per contracts/auth.yaml in backend/app/api/v1/auth.py
- [ ] T062 [US2] Implement POST /api/v1/password/change endpoint (authenticated) per contracts/auth.yaml in backend/app/api/v1/auth.py
- [ ] T063 [US2] Add session revocation on password change (all sessions except current) in backend/app/services/session_service.py
- [ ] T064 [US2] Add audit logging for password_reset_requested, password_reset_completed, password_changed events in backend/app/services/audit_service.py
- [ ] T065 [P] [US2] Create password reset request form component in frontend/augeo-admin/src/features/auth/PasswordResetRequestForm.tsx
- [ ] T066 [P] [US2] Create password reset confirm form component in frontend/augeo-admin/src/features/auth/PasswordResetConfirmForm.tsx
- [ ] T067 [P] [US2] Create password change form component in frontend/augeo-admin/src/features/settings/PasswordChangeForm.tsx
- [ ] T068 [US2] Add password reset routes to React Router in frontend/augeo-admin/src/routes/(auth)/

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can reset forgotten passwords and change passwords

---

## Phase 5: User Story 3 - Role Assignment & Permission Management (Priority: P3)

**Goal**: Administrators can assign roles to users and manage what actions different user types can perform within the system.

**Independent Test**: Create different roles (Super Admin, NPO Admin), assign them to users, and verify that users can only access features appropriate to their role.

### Tests for User Story 3

- [ ] T069 [P] [US3] Create contract test for GET /api/v1/users in backend/app/tests/contract/test_users_list.py
- [ ] T070 [P] [US3] Create contract test for POST /api/v1/users in backend/app/tests/contract/test_users_create.py
- [ ] T071 [P] [US3] Create contract test for PATCH /api/v1/users/{user_id}/role in backend/app/tests/contract/test_users_role.py
- [ ] T072 [P] [US3] Create integration test for role assignment flow in backend/app/tests/integration/test_role_assignment.py
- [ ] T073 [P] [US3] Create unit test for permission checking logic in backend/app/tests/unit/test_permissions.py

### Implementation for User Story 3

- [ ] T074 [P] [US3] Create Permission model with SQLAlchemy per data-model.md in backend/app/models/permission.py
- [ ] T075 [P] [US3] Create Alembic migration 003_create_permissions_table.py with seed permissions per data-model.md
- [ ] T076 [P] [US3] Create Pydantic schemas: UserListResponse, UserCreateRequest, RoleUpdateRequest in backend/app/schemas/users.py
- [ ] T077 [US3] Implement UserService with list_users(), create_user(), update_role(), deactivate_user() methods in backend/app/services/user_service.py
- [ ] T078 [US3] Implement PermissionService with check_permission(), get_user_permissions() methods in backend/app/services/permission_service.py
- [ ] T079 [US3] Implement GET /api/v1/users endpoint with pagination, filtering per contracts/users.yaml in backend/app/api/v1/users.py
- [ ] T080 [US3] Implement POST /api/v1/users endpoint (admin only) per contracts/users.yaml in backend/app/api/v1/users.py
- [ ] T081 [US3] Implement GET /api/v1/users/{user_id} endpoint per contracts/users.yaml in backend/app/api/v1/users.py
- [ ] T082 [US3] Implement PATCH /api/v1/users/{user_id} endpoint per contracts/users.yaml in backend/app/api/v1/users.py
- [ ] T083 [US3] Implement DELETE /api/v1/users/{user_id} endpoint (soft delete) per contracts/users.yaml in backend/app/api/v1/users.py
- [ ] T084 [US3] Implement PATCH /api/v1/users/{user_id}/role endpoint per contracts/users.yaml in backend/app/api/v1/users.py
- [ ] T085 [US3] Implement POST /api/v1/users/{user_id}/activate endpoint per contracts/users.yaml in backend/app/api/v1/users.py
- [ ] T086 [US3] Create authorization middleware with @require_role, @require_permission decorators in backend/app/middleware/auth.py
- [ ] T087 [US3] Implement role-based access control checks for all user management endpoints in backend/app/api/v1/users.py
- [ ] T088 [US3] Add audit logging for role_changed, account_deactivated events in backend/app/services/audit_service.py
- [ ] T089 [P] [US3] Create user list page component with table in frontend/augeo-admin/src/features/users/UserListPage.tsx
- [ ] T090 [P] [US3] Create user create form component in frontend/augeo-admin/src/features/users/UserCreateForm.tsx
- [ ] T091 [P] [US3] Create role assignment dialog component in frontend/augeo-admin/src/features/users/RoleAssignmentDialog.tsx
- [ ] T092 [US3] Add user management routes (admin only) to React Router in frontend/augeo-admin/src/routes/_authenticated/

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - admins can manage users and assign roles

---

## Phase 6: User Story 4 - Session Management & Security (Priority: P4)

**Goal**: The system manages user sessions securely, including automatic logout for inactive sessions and detection of suspicious login attempts.

**Independent Test**: Remain idle until session expires (wait 15+ minutes or mock time), attempt login from multiple devices, and trigger rate limiting with 6 failed login attempts.

### Tests for User Story 4

- [ ] T093 [P] [US4] Create contract test for POST /api/v1/auth/refresh in backend/app/tests/contract/test_auth_refresh.py
- [ ] T094 [P] [US4] Create integration test for token refresh flow in backend/app/tests/integration/test_token_refresh.py
- [ ] T095 [P] [US4] Create integration test for session expiration in backend/app/tests/integration/test_session_expiration.py
- [ ] T096 [P] [US4] Create integration test for rate limiting in backend/app/tests/integration/test_rate_limiting.py
- [ ] T097 [P] [US4] Create unit test for JWT blacklist logic in backend/app/tests/unit/test_jwt_blacklist.py

### Implementation for User Story 4

- [ ] T098 [P] [US4] Create Pydantic schemas: RefreshRequest, RefreshResponse in backend/app/schemas/auth.py
- [ ] T099 [US4] Implement POST /api/v1/auth/refresh endpoint per contracts/auth.yaml in backend/app/api/v1/auth.py
- [ ] T100 [US4] Implement refresh token validation and rotation in backend/app/services/auth_service.py
- [ ] T101 [US4] Implement JWT blacklist using Redis for revoked access tokens in backend/app/services/redis_service.py
- [ ] T102 [US4] Add session expiration check to auth middleware (validate session in Redis) in backend/app/middleware/auth.py
- [ ] T103 [US4] Add automatic token refresh logic to axios interceptor (handle 401 responses) in frontend/augeo-admin/src/lib/axios.ts
- [ ] T104 [US4] Add session expiration warning component (show modal 2 minutes before expiry) in frontend/augeo-admin/src/components/SessionExpirationWarning.tsx
- [ ] T105 [US4] Add device tracking: store device info (user agent, IP) with sessions in backend/app/services/session_service.py
- [ ] T106 [US4] Add audit logging for session_revoked events in backend/app/services/audit_service.py

**Checkpoint**: All user stories should now be independently functional - complete authentication system with session management

---

## Phase 7: Email Verification (Cross-Cutting Enhancement)

**Goal**: Require email verification before users can login, reducing spam accounts.

**Independent Test**: Register new account, check Redis for verification token, verify email, and confirm login is now allowed.

### Tests for Email Verification

- [ ] T107 [P] Create contract test for POST /api/v1/auth/verify-email in backend/app/tests/contract/test_email_verification.py
- [ ] T108 [P] Create contract test for POST /api/v1/auth/verify-email/resend in backend/app/tests/contract/test_email_verification.py
- [ ] T109 [P] Create integration test for email verification flow in backend/app/tests/integration/test_email_verification.py

### Implementation for Email Verification

- [ ] T110 [P] Create Pydantic schemas: EmailVerifyRequest, EmailVerifyResponse, EmailResendRequest in backend/app/schemas/auth.py
- [ ] T111 Add email_verified and is_active boolean columns to users table in Alembic migration 002_create_users_table.py
- [ ] T112 Implement email verification token utilities in backend/app/services/redis_service.py
- [ ] T113 Implement send_verification_email() in backend/app/services/email_service.py
- [ ] T114 Implement POST /api/v1/auth/verify-email endpoint per contracts/auth.yaml in backend/app/api/v1/auth.py
- [ ] T115 Implement POST /api/v1/auth/verify-email/resend endpoint per contracts/auth.yaml in backend/app/api/v1/auth.py
- [ ] T116 Add email verification check to login endpoint (block unverified users) in backend/app/api/v1/auth.py
- [ ] T117 Add verification email sending to registration endpoint in backend/app/api/v1/auth.py
- [ ] T118 Add audit logging for email_verified events in backend/app/services/audit_service.py
- [ ] T119 [P] Create email verification page component in frontend/augeo-admin/src/features/auth/EmailVerificationPage.tsx
- [ ] T120 Add email verification route to React Router in frontend/augeo-admin/src/routes/(auth)/

**Checkpoint**: Email verification complete - new users must verify email before login

---

## Phase 8: Event Staff Assignment (Role-Specific Enhancement)

**Goal**: NPO Admins can assign staff users to specific events for access control.

**Independent Test**: Create staff user, assign to event, verify staff can only access assigned events.

### Tests for Event Staff Assignment

- [ ] T121 [P] Create contract test for GET /api/v1/events/{event_id}/staff in backend/app/tests/contract/test_event_staff.py
- [ ] T122 [P] Create contract test for POST /api/v1/events/{event_id}/staff in backend/app/tests/contract/test_event_staff.py
- [ ] T123 [P] Create contract test for DELETE /api/v1/events/{event_id}/staff/{user_id} in backend/app/tests/contract/test_event_staff.py
- [ ] T124 [P] Create integration test for staff assignment flow in backend/app/tests/integration/test_event_staff_assignment.py

### Implementation for Event Staff Assignment

- [ ] T125 [P] Create EventStaff model with SQLAlchemy per data-model.md in backend/app/models/event_staff.py
- [ ] T126 [P] Create Alembic migration 006_create_event_staff_table.py
- [ ] T127 [P] Create Pydantic schemas: EventStaffListResponse, StaffAssignRequest in backend/app/schemas/users.py
- [ ] T128 Implement EventStaffService with assign_staff(), unassign_staff(), list_event_staff() methods in backend/app/services/event_staff_service.py
- [ ] T129 Implement GET /api/v1/events/{event_id}/staff endpoint per contracts/users.yaml in backend/app/api/v1/users.py
- [ ] T130 Implement POST /api/v1/events/{event_id}/staff endpoint (NPO Admin only) per contracts/users.yaml in backend/app/api/v1/users.py
- [ ] T131 Implement DELETE /api/v1/events/{event_id}/staff/{user_id} endpoint per contracts/users.yaml in backend/app/api/v1/users.py
- [ ] T132 Add event staff access checks to authorization middleware in backend/app/middleware/auth.py
- [ ] T133 [P] Create event staff assignment component in frontend/augeo-admin/src/features/events/EventStaffAssignment.tsx

**Checkpoint**: Event staff assignment complete - staff users scoped to specific events

---

## Phase 9: Row-Level Security (Multi-Tenant Data Isolation)

**Goal**: Enable PostgreSQL Row-Level Security to enforce tenant isolation at database level.

**Independent Test**: Create users in different NPOs, verify they cannot access each other's data even with direct SQL queries.

### Tests for Row-Level Security

- [ ] T134 [P] Create integration test for RLS tenant isolation in backend/app/tests/integration/test_rls_isolation.py
- [ ] T135 [P] Create integration test for super admin RLS bypass in backend/app/tests/integration/test_rls_superadmin.py

### Implementation for Row-Level Security

- [ ] T136 Create Alembic migration 008_enable_rls_policies.py to enable RLS on events, auctions, items tables
- [ ] T137 Add RLS policy for NPO-scoped users (tenant_isolation_policy) in migration 008_enable_rls_policies.py
- [ ] T138 Add RLS policy for super admin bypass in migration 008_enable_rls_policies.py
- [ ] T139 Add RLS policy for staff event access in migration 008_enable_rls_policies.py
- [ ] T140 Implement SQLAlchemy session middleware to set app.current_npo_id, app.user_role session variables in backend/app/middleware/rls.py
- [ ] T141 Update all NPO-scoped queries to leverage RLS policies in backend/app/services/

**Checkpoint**: Row-Level Security complete - database-level tenant isolation enforced

---

## Phase 10: Super Admin Bootstrap

**Goal**: Create initial super admin user from environment variables on first deployment.

**Independent Test**: Run migrations on clean database, verify super admin user created with credentials from .env.

### Implementation for Super Admin Bootstrap

- [ ] T142 Create Alembic migration 007_seed_superadmin.py that reads SUPER_ADMIN_* env vars per research.md
- [ ] T143 Add super admin creation logic with bcrypt password hashing in migration 007_seed_superadmin.py
- [ ] T144 Add environment variable validation for SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD in backend/app/core/config.py
- [ ] T145 Update quickstart.md with super admin credentials section

**Checkpoint**: Super admin bootstrap complete - first admin created on deployment

---

## Phase 11: Audit Logging

**Goal**: Log all authentication and authorization events for security auditing.

**Independent Test**: Perform various auth actions, query audit_logs table, verify all events recorded with IP and timestamp.

### Tests for Audit Logging

- [ ] T146 [P] Create integration test for audit log creation in backend/app/tests/integration/test_audit_logging.py
- [ ] T147 [P] Create unit test for audit log service in backend/app/tests/unit/test_audit_service.py

### Implementation for Audit Logging

- [ ] T148 [P] Create AuditLog model with SQLAlchemy per data-model.md in backend/app/models/audit_log.py
- [ ] T149 [P] Create Alembic migration 005_create_audit_logs_table.py
- [ ] T150 Implement AuditService with log_event() method in backend/app/services/audit_service.py
- [ ] T151 Add audit logging middleware to capture request IP and user agent in backend/app/middleware/audit.py
- [ ] T152 Integrate audit logging into all auth endpoints (login, logout, failed_login, etc.) in backend/app/api/v1/auth.py
- [ ] T153 Integrate audit logging into user management endpoints (role_changed, account_deactivated) in backend/app/api/v1/users.py

**Checkpoint**: Audit logging complete - all security events tracked

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T154 [P] Add API documentation with OpenAPI/Swagger at /docs endpoint in backend/app/main.py
- [ ] T155 [P] Create comprehensive README.md in backend/ with setup instructions
- [ ] T156 [P] Create comprehensive README.md in frontend/augeo-admin/ with setup instructions
- [ ] T157 [P] Add error handling for database connection failures in backend/app/core/database.py
- [ ] T158 [P] Add error handling for Redis connection failures in backend/app/core/redis.py
- [ ] T159 [P] Add error handling for email service failures in backend/app/services/email_service.py
- [ ] T160 [P] Implement health check endpoint at /health in backend/app/api/health.py
- [ ] T161 [P] Add monitoring/metrics endpoint at /metrics in backend/app/api/metrics.py
- [ ] T162 Code cleanup: Remove unused imports, add type hints, fix linting issues across backend/
- [ ] T163 [P] Performance optimization: Add database query indexes per data-model.md
- [ ] T164 [P] Performance optimization: Add Redis caching for permission checks in backend/app/services/permission_service.py
- [ ] T165 [P] Security hardening: Add CORS configuration with allowed origins in backend/app/main.py
- [ ] T166 [P] Security hardening: Add rate limiting to all public endpoints in backend/app/middleware/rate_limit.py
- [ ] T167 [P] Security hardening: Add request ID tracing for debugging in backend/app/middleware/request_id.py
- [ ] T168 [P] Add E2E tests with Playwright for critical user journeys in frontend/augeo-admin/e2e/
- [ ] T169 Run quickstart.md validation: Setup Docker Compose, run migrations, test auth flow end-to-end
- [ ] T170 Update .github/copilot-instructions.md with auth feature completion

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (Registration & Login) - No dependencies on other stories
  - User Story 2 (Password Recovery) - Depends on US1 (needs User model and AuthService)
  - User Story 3 (Role Management) - Depends on US1 (needs User model and auth)
  - User Story 4 (Session Management) - Depends on US1 (needs login/logout)
- **Email Verification (Phase 7)**: Depends on US1 (extends registration/login)
- **Event Staff (Phase 8)**: Depends on US3 (needs role management)
- **RLS (Phase 9)**: Depends on US1, US3 (needs users and roles)
- **Super Admin (Phase 10)**: Depends on US1 (needs User model)
- **Audit Logging (Phase 11)**: Can start after Foundational, runs parallel to user stories
- **Polish (Phase 12)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - FOUNDATION FOR ALL OTHER STORIES
- **User Story 2 (P2)**: Requires US1 complete (needs User, AuthService)
- **User Story 3 (P3)**: Requires US1 complete (needs User, auth middleware)
- **User Story 4 (P4)**: Requires US1 complete (needs login/logout flows)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Once US1 is complete, US2, US3, US4 can be worked on in parallel (with caution on shared files)
- Email Verification (Phase 7) and Audit Logging (Phase 11) can run in parallel with user stories
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task T023: "Contract test for POST /api/v1/auth/register"
Task T024: "Contract test for POST /api/v1/auth/login"
Task T025: "Contract test for POST /api/v1/auth/logout"
Task T026: "Integration test for registration → login flow"
Task T027: "Unit test for JWT token creation/verification"
Task T028: "Unit test for password hashing"

# After tests fail, launch all models together:
Task T029: "Create User model"
Task T031: "Create Session model"

# Launch all frontend components together:
Task T045: "Create login form component"
Task T046: "Create registration form component"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T011)
2. Complete Phase 2: Foundational (T012-T022) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (T023-T050)
4. Complete Phase 10: Super Admin Bootstrap (T142-T145) - needed for first admin
5. **STOP and VALIDATE**: Test User Story 1 independently using quickstart.md
6. Deploy/demo if ready - Users can register, login, logout

### Incremental Delivery (Recommended)

1. Complete Setup + Foundational → Foundation ready (T001-T022)
2. Add Super Admin Bootstrap (T142-T145) → First admin created
3. Add User Story 1 (T023-T050) → Test independently → Deploy/Demo (MVP! ✅)
4. Add User Story 2 (T051-T068) → Test independently → Deploy/Demo (Password recovery ✅)
5. Add Email Verification (T107-T120) → Test independently → Deploy/Demo (Email verified users ✅)
6. Add User Story 3 (T069-T092) → Test independently → Deploy/Demo (Role management ✅)
7. Add Audit Logging (T146-T153) → Deploy/Demo (Security audit trail ✅)
8. Add User Story 4 (T093-T106) → Test independently → Deploy/Demo (Session management ✅)
9. Add Event Staff (T121-T133) → Deploy/Demo (Event-scoped staff ✅)
10. Add RLS (T134-T141) → Deploy/Demo (Database-level isolation ✅)
11. Add Polish (T154-T170) → Final production-ready release ✅

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T022)
2. Team completes Super Admin Bootstrap (T142-T145)
3. Once Foundational is done:
   - Developer A: User Story 1 (T023-T050)
   - Developer B: Audit Logging (T146-T153) - runs parallel
4. Once US1 is done:
   - Developer A: User Story 2 (T051-T068)
   - Developer B: Email Verification (T107-T120)
   - Developer C: User Story 3 (T069-T092)
5. Stories complete and integrate independently

---

## Task Summary

**Total Tasks**: 170

**Tasks by Phase**:
- Phase 1 (Setup): 11 tasks
- Phase 2 (Foundational): 11 tasks (BLOCKING)
- Phase 3 (User Story 1 - Registration & Login): 28 tasks ← MVP
- Phase 4 (User Story 2 - Password Recovery): 18 tasks
- Phase 5 (User Story 3 - Role Management): 24 tasks
- Phase 6 (User Story 4 - Session Management): 14 tasks
- Phase 7 (Email Verification): 14 tasks
- Phase 8 (Event Staff Assignment): 13 tasks
- Phase 9 (Row-Level Security): 8 tasks
- Phase 10 (Super Admin Bootstrap): 4 tasks
- Phase 11 (Audit Logging): 8 tasks
- Phase 12 (Polish): 17 tasks

**Parallel Tasks**: 83 tasks marked [P] can run in parallel

**MVP Scope** (Minimum Viable Product):
- Phase 1: Setup (T001-T011)
- Phase 2: Foundational (T012-T022)
- Phase 3: User Story 1 (T023-T050)
- Phase 10: Super Admin Bootstrap (T142-T145)
- **Total MVP**: 54 tasks

**Independent Test Criteria**:
- US1: Create account → logout → login → access protected endpoint
- US2: Request password reset → receive email → reset password → login with new password
- US3: Create user → assign role → verify role-based access → change role → verify updated access
- US4: Login → wait for expiration → verify re-auth required → trigger rate limit → verify blocking

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are REQUIRED for this security-critical feature
- Follow quickstart.md for local development setup
- Use data-model.md for database schema reference
- Use contracts/ for API endpoint specifications
- Use research.md for architecture decisions

---

**Status**: Ready for implementation
**Next Step**: Begin Phase 1 (Setup) → T001
**Version**: 1.0.0
**Date**: October 20, 2025
