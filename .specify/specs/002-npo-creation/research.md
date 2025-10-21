# Research: NPO Creation and Management

**Date**: 2025-10-19
**Status**: Phase 0 - Research Complete

## Research Tasks Completed

### 1. Multi-Tenant NPO Data Model Design

**Decision**: Extend existing multi-tenant architecture with NPO-specific entities
**Rationale**:
- Leverages existing `tenant_id` pattern from constitution
- Maintains data isolation between NPOs
- Aligns with PostgreSQL Row-Level Security approach already established

**Implementation Approach**:
- `NPO` entity serves as the tenant root with `npo_id` as tenant identifier
- All NPO-related data includes `npo_id` foreign key for isolation
- Existing authentication system extended with NPO-scoped roles

**Alternatives Considered**:
- Separate databases per NPO (rejected: unnecessary complexity for current scale)
- Schema-per-tenant (rejected: migration complexity, not aligned with constitution)

### 2. File Upload Security for NPO Branding

**Decision**: Azure Blob Storage with signed URLs and content validation
**Rationale**:
- Aligns with constitution's Azure-first infrastructure approach
- Built-in CDN capabilities for global performance
- Proper security controls with time-limited access URLs

**Implementation Details**:
- File type validation: PNG, JPG, SVG for logos (max 5MB)
- Virus scanning via Azure Defender for Storage
- Automatic image optimization and multiple size generation
- Secure upload flow: client → signed URL → direct to blob storage

**Alternatives Considered**:
- Local file storage (rejected: not scalable, backup complexity)
- Third-party services like Cloudinary (rejected: unnecessary cost for current needs)

### 3. Staff Invitation and Role Management System

**Decision**: JWT-based invitation tokens with role-scoped permissions
**Rationale**:
- Integrates with existing OAuth2/JWT authentication system
- Supports time-limited invitations with automatic expiry
- Role-based access control already established in constitution

**Implementation Flow**:
1. NPO Admin creates invitation with specified role
2. System generates JWT token with invitation claims
3. Email sent with invitation link containing token
4. Recipient accepts → creates account → token validated → role assigned
5. Failed/expired invitations tracked for audit

**Role Hierarchy**:
- SuperAdmin: Platform-wide administration
- NPO Admin: Full NPO management, can invite Co-Admins and Staff
- NPO Co-Admin: NPO management, can invite Staff (no Admin privileges)
- NPO Staff: Event management within NPO scope

### 4. SuperAdmin Approval Workflow Design

**Decision**: State machine-based application workflow with audit trails
**Rationale**:
- Clear state transitions prevent inconsistent application status
- Full audit trail for compliance and support purposes
- Supports both manual and automated approval criteria

**Application States**:
- `DRAFT`: Initial creation, can be edited
- `SUBMITTED`: Locked for review, awaiting SuperAdmin action
- `UNDER_REVIEW`: SuperAdmin actively reviewing
- `APPROVED`: NPO activated, can create events and send invitations
- `REJECTED`: Application denied with reasons, can be resubmitted
- `SUSPENDED`: Temporarily disabled (post-approval enforcement)

**Review Criteria Automation**:
- Tax ID validation via external API (if available)
- Duplicate organization name detection
- Required field completeness check
- Automated flagging for manual review

### 5. Legal Agreement Management (EULA/Terms)

**Decision**: Versioned legal documents with tracking and re-acceptance workflow
**Rationale**:
- GDPR compliance requires proper consent tracking
- Legal document updates need user re-acceptance
- Audit trail essential for legal protection

**Implementation Features**:
- Document versioning with effective dates
- User acceptance tracking with timestamps and IP addresses
- Forced re-acceptance workflow when terms update
- Export capability for legal compliance requests

**Document Types**:
- End User License Agreement (EULA)
- Terms of Service
- Privacy Policy
- Data Processing Agreement (for EU NPOs)

### 6. Social Media Integration Best Practices

**Decision**: URL validation with platform-specific regex patterns
**Rationale**:
- Prevents invalid social media links in NPO profiles
- Consistent formatting for display purposes
- Future integration potential with social APIs

**Supported Platforms**:
- Facebook: Validate page URL format
- Twitter/X: Handle with @ prefix validation
- Instagram: Username validation
- LinkedIn: Organization page URL
- YouTube: Channel URL validation
- Custom: Generic URL validation for other platforms

**Validation Rules**:
- URL accessibility check (HTTP 200 response)
- Platform-specific format validation
- Character limits and special character handling
- Optional preview generation for verified URLs

### 7. Branding Color System Implementation

**Decision**: CSS custom properties with theme inheritance
**Rationale**:
- Dynamic theming without CSS rebuilds
- Consistent color application across components
- Accessibility compliance with contrast checking

**Color Properties**:
- Primary color: Main brand color
- Secondary color: Accent/highlight color
- Background variants: Light/dark mode support
- Text colors: Automatic contrast calculation
- Success/warning/error: Semantic color overrides

**Technical Implementation**:
- Runtime CSS custom property injection
- Color picker with accessibility warnings
- Preview mode for real-time brand visualization
- Export to CSS variables for external use

## Key Dependencies Identified

### Backend Dependencies
- `Pillow`: Image processing and validation
- `python-magic`: File type detection
- `azure-storage-blob`: Blob storage integration
- `pydantic-extra-types`: Enhanced validation (emails, URLs)

### Frontend Dependencies
- `react-colorful`: Color picker component
- `react-hook-form`: Form validation and management
- `@tanstack/react-query`: Server state management
- `react-dropzone`: File upload interface

### Infrastructure Requirements
- Azure Blob Storage container for NPO assets
- Email service integration (SendGrid/Azure Communication Services)
- DNS configuration for subdomain routing (future feature)

## Performance Considerations

### Database Optimization
- Indexed fields: `npo_id`, `application_status`, `created_at`
- Composite indexes for common query patterns
- Soft delete with archive table for compliance

### Caching Strategy
- NPO profile data: 1-hour TTL in Redis
- Legal document content: 24-hour TTL (updates rare)
- Application status: Real-time, no caching

### File Upload Performance
- Client-side image compression before upload
- Progressive image loading in UI
- CDN caching for approved NPO assets

## Security Measures

### Data Validation
- Server-side validation mirrors client-side rules
- SQL injection prevention via parameterized queries
- XSS protection with output encoding

### Access Control
- Role-based endpoint protection via FastAPI dependencies
- NPO data isolation enforced at database level
- Invitation token single-use enforcement

### Audit Logging
- All NPO creation/modification events logged
- SuperAdmin review actions tracked
- Legal agreement acceptance recorded with metadata

## Integration Points

### Existing System Integration
- Authentication: Extends current OAuth2/JWT system
- Multi-tenancy: Uses established `tenant_id` pattern
- Email: Leverages existing notification infrastructure
- File storage: Integrates with planned Azure Blob architecture

### Future Feature Preparation
- Event creation: NPO approval status gates event functionality
- Payment processing: NPO verification required for Stripe onboarding
- Analytics: NPO-scoped reporting and dashboards

## Compliance Requirements

### GDPR Considerations
- Data export capability for NPO administrators
- Right to deletion with proper anonymization
- Consent withdrawal handling for legal agreements

### Financial Compliance
- NPO tax status verification (US: 501(c)(3), international equivalents)
- Anti-money laundering (AML) basic checks
- Documentation retention for audit purposes

## Development Approach

### Phase 1 Implementation Order
1. Database models and migrations
2. Backend API endpoints with validation
3. Basic frontend forms and workflows
4. File upload integration
5. Email notification system
6. SuperAdmin review interface

### Testing Strategy
- Unit tests: Service layer business logic
- Integration tests: API endpoint workflows
- E2E tests: Complete NPO creation and approval flow
- Security tests: Access control and data isolation

### Deployment Considerations
- Feature flag for gradual rollout
- Database migration coordination
- Azure resources provisioning
- Email template configuration

## Risk Mitigation

### Technical Risks
- File upload abuse: Size limits, type validation, virus scanning
- Database performance: Proper indexing, query optimization
- Email deliverability: Sender reputation, bounce handling

### Business Risks
- Manual approval bottleneck: Automated criteria where possible
- Legal liability: Proper terms acceptance tracking
- User experience: Progressive enhancement for complex forms

### Security Risks
- Data breaches: Encryption, access logging, regular audits
- Social engineering: Multi-factor authentication for sensitive operations
- Compliance violations: Regular legal document reviews, audit trails

## Success Metrics

### Technical Metrics
- NPO creation completion rate >90%
- Application approval time <2 business days average
- File upload success rate >99%
- API response time <300ms p95

### Business Metrics
- NPO application rejection rate <10%
- Time from approval to first event <1 week
- User satisfaction with onboarding process >4.5/5
- Support tickets related to NPO setup <5% of total

### Compliance Metrics
- Legal agreement acceptance rate 100%
- Audit trail completeness 100%
- Data export request fulfillment <24 hours
- Security incident count: 0
