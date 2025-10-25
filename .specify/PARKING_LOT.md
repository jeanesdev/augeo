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

### Email Integration Tests (T055)
- **Status**: Deferred - Covered by contract tests
- **Phase**: Phase 4 (User Story 2)
- **Reason**: Token extraction from mock emails requires additional test infrastructure
- **Current Coverage**: Contract tests validate endpoint behavior without email content parsing
- **Revisit When**:
  - Real email sending implemented (Azure Communication Services)
  - Need end-to-end email verification flow tests
- **Estimated Effort**: 2-3 days

### Audit Service Unit Tests (T147)
- **Status**: Deferred - Integration tests provide sufficient coverage
- **Phase**: Phase 11 (Audit Logging)
- **Reason**: Integration tests provide 88% coverage of audit logging functionality
- **Current Coverage**: 4/4 integration tests passing (test_audit_logging.py)
- **Revisit When**:
  - Audit methods become more complex with business logic
  - Need to test edge cases not covered by integration tests
  - Code coverage requirements increase above 90%
- **Estimated Effort**: 1-2 days

### Audit Logging Middleware (T151)
- **Status**: Deferred - Endpoint-level capture preferred
- **Phase**: Phase 11 (Audit Logging)
- **Reason**: IP address and user agent captured at endpoint level provides more context
- **Current Approach**: Endpoints pass IP/UA directly to audit methods
- **ADR**: [ADR-002: Audit Logging Database Persistence](./.specify/adr/002-audit-logging-database-persistence.md)
- **Revisit When**:
  - Need centralized request metadata capture
  - Want to audit all requests (not just security events)
  - Performance optimization needed (avoid duplicate extraction)
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
- **Status**: Blocked on infrastructure deployment (Spec 004)
- **Blocking Issue**: Requires Azure Communication Services, verified domain, DNS configuration, and production URLs
- **Current State**: Mock mode working (logs to console) - sufficient for development and testing
- **Files**: `backend/app/services/email_service.py`
- **Dependencies**:
  - Azure Communication Services Email resource
  - Domain ownership verification (augeo.app or similar)
  - DNS records (SPF, DKIM, DMARC) for email deliverability
  - Production frontend URLs for email links
  - azure-communication-email package
  - AZURE_COMMUNICATION_CONNECTION_STRING environment variable
  - EMAIL_FROM_ADDRESS configuration
- **Impact**: Cannot send real emails (password reset, verification, user invitations)
- **Priority**: Required for production launch - **blocked until Spec 004 (Cloud Infrastructure & Deployment)**
- **Next Steps**:
  1. Create Spec 004: Cloud Infrastructure & Deployment
  2. Plan full Azure architecture (App Service, DNS, monitoring, etc.)
  3. Implement email as part of complete deployment
- **Estimated Effort**: 1-2 days (after infrastructure is deployed)
- **Related Specs**: Spec 004 (Cloud Infrastructure & Deployment) - Not yet created

### IP Address Capture in Audit Logs
- **Status**: Currently set to None
- **Service**: `backend/app/services/audit_service.py`
- **Files**: All audit method calls in endpoints
- **Required**:
  - Extract IP from `request.client.host` in FastAPI
  - Handle proxies/load balancers (X-Forwarded-For header)
  - Pass IP address parameter to all audit methods
  - Privacy/compliance considerations
- **Impact**: Audit logs missing source IP for security investigations
- **Priority**: Should implement before production
- **Estimated Effort**: 1-2 days

## Blocked Items

### Real Email Sending (Production)
- **Blocked By**: Missing Spec 004 (Cloud Infrastructure & Deployment)
- **Status**: Need to create comprehensive deployment spec before implementing production email
- **Reason**: Email requires domain, DNS, Azure resources, and production URLs - should be done holistically
- **Current Workaround**: Mock email mode works for development/testing
- **Tasks Affected**:
  - T057: Email service implementation (partially complete - mock mode working)
  - Production deployment of password reset feature
  - Production deployment of email verification feature
  - User invitation emails
- **Next Action**: Create Spec 004 to plan Azure infrastructure, domain setup, DNS, CI/CD, and monitoring
- **Priority**: Medium - Not blocking current development, required before production launch

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

**Last Updated**: 2025-10-25
**Maintained By**: Development Team
**Review Cadence**: Update after each phase completion
