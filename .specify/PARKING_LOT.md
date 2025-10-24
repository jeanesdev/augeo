# Parking Lot

Items that are deferred, blocked, or waiting for future consideration.

## Deferred Features

### Database Permission Table (T074-T075)
- **Status**: Deferred - Using service-based permissions instead
- **Phase**: Phase 5 (User Story 3)
- **Reason**: Simpler and faster for MVP; 5 roles with clear hierarchy don't require database-backed permissions
- **ADR**: [ADR-001: Service-Based Permissions](./.specify/adr/001-service-based-permissions.md)
- **Revisit When**:
  - Custom permissions needed per NPO
  - Dynamic role creation required
  - Compliance requires permission audit trail
- **Estimated Effort**: 5-8 days to implement fully

### Email Integration Tests (T055, T134)
- **Status**: Deferred - Covered by contract tests
- **Phase**: Phase 4 (User Story 2)
- **Reason**: Token extraction from mock emails requires additional test infrastructure
- **Current Coverage**: Contract tests validate endpoint behavior without email content parsing
- **Revisit When**:
  - Real email sending implemented (Azure Communication Services)
  - Need end-to-end email verification flow tests
- **Estimated Effort**: 2-3 days

## Technical Debt

### Contract Test Failures
- **Status**: 22/28 contract tests need debugging
- **Files Affected**: Various contract test files in `backend/app/tests/contract/`
- **Impact**: Medium (unit/integration tests passing)
- **Priority**: Should fix before Phase 6
- **Estimated Effort**: 2-3 days

### Mypy Type Annotation Errors
- **Status**: 27 type annotation errors
- **Command**: `cd backend && poetry run mypy app`
- **Impact**: Low (code runs correctly)
- **Priority**: Nice-to-have for code quality
- **Estimated Effort**: 1-2 days

### Email Service Production Implementation
- **Status**: Mock mode only (logs to console)
- **Service**: Azure Communication Services integration pending
- **Files**: `backend/app/services/email_service.py`
- **Required**:
  - AZURE_COMMUNICATION_CONNECTION_STRING environment variable
  - EMAIL_FROM_ADDRESS configuration
  - azure-communication-email package
- **Impact**: Cannot send real emails (password reset, verification)
- **Priority**: Required for production launch
- **Estimated Effort**: 1-2 days

### Audit Log Database Persistence
- **Status**: Logs to stdout/console only
- **Service**: `backend/app/services/audit_service.py`
- **Alternative**: Log aggregation service (Azure App Insights, ELK)
- **Database Table**: Not implemented (would be Phase 11: T148-T153)
- **Impact**: No queryable audit history
- **Priority**: Required for compliance/production
- **Estimated Effort**: 3-5 days (table + migration + service + admin UI)

## Blocked Items

None currently.

## Future Enhancements

### Row-Level Security (RLS)
- **Mentioned In**: research.md - "Phase 1 requirement (was incorrectly deferred to Phase 2)"
- **Status**: Not yet implemented
- **Purpose**: PostgreSQL RLS for data isolation between NPOs
- **Priority**: Required before multi-NPO support
- **Estimated Effort**: 5-8 days

### Structured Food Options
- **Mentioned In**: 003-event-creation-ability spec
- **Status**: Free-text field in MVP, structured options deferred
- **Purpose**: Better UX for menu/dietary info entry
- **Priority**: Nice-to-have enhancement
- **Estimated Effort**: 3-5 days

## Decisions Needed

None currently - all active work has clear direction.

---

**Last Updated**: 2025-10-24
**Maintained By**: Development Team
**Review Cadence**: Update after each phase completion
