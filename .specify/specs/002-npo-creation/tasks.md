---
description: "Task list for NPO Creation and Management feature implementation"
---

# Tasks: NPO Creation and Management

**Input**: Design documents from `/specs/002-npo-creation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/npo-management-api.yaml

**Tests**: Tests are included and REQUIRED per constitution (production-grade quality)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/app/` (following existing structure)
- **Frontend**: `frontend/augeo-admin/src/`
- **Tests**: `backend/app/tests/` and `frontend/augeo-admin/tests/`

---

## Phase 0: Setup (Shared Infrastructure) ✅ COMPLETE

**Purpose**: Project initialization and basic structure

- [x] T001 Review existing authentication system (OAuth2/JWT) and multi-tenant patterns in backend/app/
- [x] T002 [P] Setup Azure Blob Storage container for NPO assets (logo uploads)
- [x] T003 [P] Configure email service (SendGrid/Azure Communication Services) credentials
- [x] T004 Add Python dependencies to backend/pyproject.toml: Pillow, python-magic, azure-storage-blob, pydantic-extra-types
- [x] T005 Add frontend dependencies to frontend/augeo-admin/package.json: react-colorful, react-dropzone, @tanstack/react-query

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create database migration for NPO tables in backend/alembic/versions/: npo, npo_application, npo_member, npo_branding, invitation, legal_document, legal_agreement_acceptance
- [ ] T007 Create base NPO model in backend/app/models/npo.py with status enum (DRAFT, PENDING_APPROVAL, APPROVED, SUSPENDED, REJECTED)
- [ ] T008 [P] Create NPOApplication model in backend/app/models/npo_application.py with workflow states
- [ ] T009 [P] Create NPOMember model in backend/app/models/npo_member.py with role hierarchy (ADMIN, CO_ADMIN, STAFF)
- [ ] T010 [P] Create NPOBranding model in backend/app/models/npo_branding.py for visual identity
- [ ] T011 [P] Create Invitation model in backend/app/models/invitation.py with JWT token management
- [ ] T012 [P] Create LegalDocument model in backend/app/models/legal_document.py with versioning
- [ ] T013 [P] Create LegalAgreementAcceptance model in backend/app/models/legal_agreement_acceptance.py for compliance tracking
- [ ] T014 Run database migration: cd backend && poetry run alembic upgrade head
- [ ] T015 Create database indexes for performance: npo_status, npo_member_npo_id, application_status, invitation_email_status
- [ ] T016 [P] Create Pydantic schemas in backend/app/schemas/npo_schemas.py: CreateNPORequest, UpdateNPORequest, NPODetail, NPOSummary
- [ ] T017 [P] Create Pydantic schemas in backend/app/schemas/application_schemas.py: ApplicationDetail, ReviewRequest
- [ ] T018 [P] Create Pydantic schemas in backend/app/schemas/member_schemas.py: CreateInvitationRequest, MemberDetail
- [ ] T019 [P] Create Pydantic schemas in backend/app/schemas/branding_schemas.py: UpdateBrandingRequest, BrandingDetail
- [ ] T020 Create NPO permission service in backend/app/services/npo_permission_service.py with role-based checks
- [ ] T021 Create file upload service in backend/app/services/file_upload_service.py with Azure Blob integration and signed URLs
- [ ] T022 Create email notification service in backend/app/services/email_notification_service.py for invitations and status updates
- [ ] T023 Extend audit logging in backend/app/services/audit_service.py for NPO operations
- [ ] T024 [P] Setup frontend NPO store in frontend/augeo-admin/src/stores/npo-store.ts using Zustand
- [ ] T025 [P] Create NPO API client in frontend/augeo-admin/src/features/npo-management/services/npo-api.ts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - NPO Administrator Creating Organization Profile (Priority: P1) 🎯 MVP

**Goal**: Enable NPO administrators to create and configure their organization's profile with all required details

**Independent Test**: Admin can create NPO, save as draft, edit details, and see it in their NPO list

### Tests for User Story 1 ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T026 [P] [US1] Contract test for POST /api/v1/npos endpoint in backend/app/tests/contract/test_npo_creation.py
- [ ] T027 [P] [US1] Contract test for GET /api/v1/npos and GET /api/v1/npos/{id} in backend/app/tests/contract/test_npo_retrieval.py
- [ ] T028 [P] [US1] Contract test for PUT /api/v1/npos/{id} in backend/app/tests/contract/test_npo_update.py
- [ ] T029 [P] [US1] Integration test for complete NPO creation workflow in backend/app/tests/integration/test_npo_creation_flow.py
- [ ] T030 [P] [US1] Unit test for NPO name uniqueness validation in backend/app/tests/unit/test_npo_validation.py

### Implementation for User Story 1

- [ ] T031 [US1] Implement NPOService.create_npo() in backend/app/services/npo_service.py with validation and multi-tenant isolation
- [ ] T032 [US1] Implement NPOService.get_npo() with permission checking in backend/app/services/npo_service.py
- [ ] T033 [US1] Implement NPOService.update_npo() with draft-only editing in backend/app/services/npo_service.py
- [ ] T034 [US1] Implement NPOService.list_user_npos() with pagination in backend/app/services/npo_service.py
- [ ] T035 [US1] Create POST /api/v1/npos endpoint in backend/app/api/v1/npo_endpoints.py
- [ ] T036 [US1] Create GET /api/v1/npos endpoint with filtering in backend/app/api/v1/npo_endpoints.py
- [ ] T037 [US1] Create GET /api/v1/npos/{id} endpoint in backend/app/api/v1/npo_endpoints.py
- [ ] T038 [US1] Create PUT /api/v1/npos/{id} endpoint in backend/app/api/v1/npo_endpoints.py
- [ ] T039 [US1] Add validation for NPO name uniqueness, tax ID format, and email in backend/app/services/npo_service.py
- [ ] T040 [US1] Add audit logging for NPO creation and updates in backend/app/services/npo_service.py
- [ ] T041 [P] [US1] Create NpoCreationForm component in frontend/augeo-admin/src/features/npo-management/components/NpoCreationForm.tsx with react-hook-form
- [ ] T042 [P] [US1] Create multi-step form navigation in NpoCreationForm (Basic Info, Contact, Branding, Review)
- [ ] T043 [US1] Implement form validation matching backend rules in frontend
- [ ] T044 [US1] Create CreateNpoPage in frontend/augeo-admin/src/features/npo-management/pages/CreateNpoPage.tsx
- [ ] T045 [US1] Create NpoListPage in frontend/augeo-admin/src/features/npo-management/pages/NpoListPage.tsx with status filtering
- [ ] T046 [US1] Create useNpoCreation hook in frontend/augeo-admin/src/features/npo-management/hooks/useNpoCreation.ts
- [ ] T047 [US1] Add routing for NPO creation and list pages in frontend router

**Checkpoint**: At this point, User Story 1 should be fully functional - admin can create, edit, and view NPOs

---

## Phase 3: User Story 2 - NPO Administrator Customizing Branding (Priority: P1) 🎯 MVP

**Goal**: Enable NPO administrators to customize visual identity with colors, logo, and social media links

**Independent Test**: Admin can upload logo, set colors, add social media links, and see real-time preview

### Tests for User Story 2 ⚠️

- [ ] T048 [P] [US2] Contract test for GET /api/v1/npos/{id}/branding in backend/app/tests/contract/test_branding_endpoints.py
- [ ] T049 [P] [US2] Contract test for PUT /api/v1/npos/{id}/branding in backend/app/tests/contract/test_branding_endpoints.py
- [ ] T050 [P] [US2] Contract test for POST /api/v1/npos/{id}/logo/upload-url in backend/app/tests/contract/test_file_upload.py
- [ ] T051 [P] [US2] Integration test for logo upload workflow in backend/app/tests/integration/test_logo_upload_flow.py
- [ ] T052 [P] [US2] Unit test for color validation and contrast checking in backend/app/tests/unit/test_color_validation.py
- [ ] T053 [P] [US2] Unit test for social media URL validation in backend/app/tests/unit/test_social_media_validation.py

### Implementation for User Story 2

- [ ] T054 [US2] Implement BrandingService.get_branding() in backend/app/services/branding_service.py
- [ ] T055 [US2] Implement BrandingService.update_branding() with color validation in backend/app/services/branding_service.py
- [ ] T056 [US2] Implement FileUploadService.generate_upload_url() for Azure Blob signed URLs in backend/app/services/file_upload_service.py
- [ ] T057 [US2] Implement FileUploadService.validate_image() with Pillow for file type/size checks in backend/app/services/file_upload_service.py
- [ ] T058 [US2] Add social media URL validation patterns (Facebook, Twitter, Instagram, LinkedIn, YouTube) in backend/app/services/branding_service.py
- [ ] T059 [US2] Create GET /api/v1/npos/{id}/branding endpoint in backend/app/api/v1/branding_endpoints.py
- [ ] T060 [US2] Create PUT /api/v1/npos/{id}/branding endpoint in backend/app/api/v1/branding_endpoints.py
- [ ] T061 [US2] Create POST /api/v1/npos/{id}/logo/upload-url endpoint in backend/app/api/v1/branding_endpoints.py
- [ ] T062 [P] [US2] Create BrandingConfiguration component in frontend/augeo-admin/src/features/npo-management/components/BrandingConfiguration.tsx
- [ ] T063 [P] [US2] Integrate react-colorful color picker with accessibility contrast warnings
- [ ] T064 [P] [US2] Create LogoUpload component with react-dropzone in frontend/augeo-admin/src/features/npo-management/components/LogoUpload.tsx
- [ ] T065 [US2] Implement direct-to-Azure upload with signed URLs in LogoUpload component
- [ ] T066 [US2] Create SocialMediaLinks component with platform-specific validation in frontend/augeo-admin/src/features/npo-management/components/SocialMediaLinks.tsx
- [ ] T067 [US2] Create real-time branding preview component in frontend/augeo-admin/src/features/npo-management/components/BrandingPreview.tsx
- [ ] T068 [US2] Add branding section to NpoSettingsPage in frontend/augeo-admin/src/features/npo-management/pages/NpoSettingsPage.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 work independently - admin can fully brand their NPO

---

## Phase 4: User Story 3 - NPO Administrator Inviting Co-Admins and Staff (Priority: P1) 🎯 MVP

**Goal**: Enable NPO administrators to invite team members with role-based permissions

**Independent Test**: Admin can send invitations, recipients receive emails with tokens, can accept and join NPO

### Tests for User Story 3 ⚠️

- [ ] T069 [P] [US3] Contract test for GET /api/v1/npos/{id}/members in backend/app/tests/contract/test_member_endpoints.py
- [ ] T070 [P] [US3] Contract test for POST /api/v1/npos/{id}/members in backend/app/tests/contract/test_member_endpoints.py
- [ ] T071 [P] [US3] Contract test for POST /api/v1/invitations/{id}/accept in backend/app/tests/contract/test_invitation_endpoints.py
- [ ] T072 [P] [US3] Integration test for invitation creation and acceptance workflow in backend/app/tests/integration/test_invitation_flow.py
- [ ] T073 [P] [US3] Unit test for role hierarchy validation (ADMIN > CO_ADMIN > STAFF) in backend/app/tests/unit/test_role_permissions.py
- [ ] T074 [P] [US3] Unit test for invitation token generation and validation in backend/app/tests/unit/test_invitation_tokens.py

### Implementation for User Story 3

- [ ] T075 [US3] Implement InvitationService.create_invitation() with JWT token generation in backend/app/services/invitation_service.py
- [ ] T076 [US3] Implement InvitationService.accept_invitation() with token validation in backend/app/services/invitation_service.py
- [ ] T077 [US3] Implement InvitationService.revoke_invitation() in backend/app/services/invitation_service.py
- [ ] T078 [US3] Add invitation expiry check (7 days) and automatic cleanup in backend/app/services/invitation_service.py
- [ ] T079 [US3] Implement MemberService.get_members() with role filtering in backend/app/services/member_service.py
- [ ] T080 [US3] Implement MemberService.update_member() with permission checks in backend/app/services/member_service.py
- [ ] T081 [US3] Implement MemberService.remove_member() with admin protection in backend/app/services/member_service.py
- [ ] T082 [US3] Add email notification for invitation sent in backend/app/services/email_notification_service.py
- [ ] T083 [US3] Add email notification for invitation accepted in backend/app/services/email_notification_service.py
- [ ] T084 [US3] Create invitation email template with token link
- [ ] T085 [US3] Create GET /api/v1/npos/{id}/members endpoint in backend/app/api/v1/member_endpoints.py
- [ ] T086 [US3] Create POST /api/v1/npos/{id}/members endpoint with role validation in backend/app/api/v1/member_endpoints.py
- [ ] T087 [US3] Create PUT /api/v1/npos/{id}/members/{memberId} endpoint in backend/app/api/v1/member_endpoints.py
- [ ] T088 [US3] Create DELETE /api/v1/npos/{id}/members/{memberId} endpoint in backend/app/api/v1/member_endpoints.py
- [ ] T089 [US3] Create POST /api/v1/invitations/{id}/accept endpoint in backend/app/api/v1/invitation_endpoints.py
- [ ] T090 [P] [US3] Create StaffInvitation component in frontend/augeo-admin/src/features/npo-management/components/StaffInvitation.tsx
- [ ] T091 [P] [US3] Create MemberList component with role badges in frontend/augeo-admin/src/features/npo-management/components/MemberList.tsx
- [ ] T092 [US3] Create invitation form with email and role selection
- [ ] T093 [US3] Add member management to NpoSettingsPage
- [ ] T094 [US3] Create InvitationAcceptancePage for token validation in frontend/augeo-admin/src/features/npo-management/pages/InvitationAcceptancePage.tsx
- [ ] T095 [US3] Add routing for invitation acceptance: /invitations/{id}/accept?token=xxx

**Checkpoint**: At this point, User Stories 1, 2, AND 3 work independently - team collaboration enabled

---

## Phase 5: User Story 4 - SuperAdmin Reviewing NPO Applications (Priority: P2)

**Goal**: Enable SuperAdmin to review, approve, or reject NPO applications with feedback

**Independent Test**: SuperAdmin can see pending applications, review details, approve/reject with notes

### Tests for User Story 4 ⚠️

- [ ] T096 [P] [US4] Contract test for GET /api/v1/admin/npos/applications in backend/app/tests/contract/test_admin_endpoints.py
- [ ] T097 [P] [US4] Contract test for POST /api/v1/admin/npos/{id}/applications/{appId}/review in backend/app/tests/contract/test_admin_endpoints.py
- [ ] T098 [P] [US4] Contract test for POST /api/v1/npos/{id}/submit in backend/app/tests/contract/test_application_submission.py
- [ ] T099 [P] [US4] Integration test for complete application submission and approval workflow in backend/app/tests/integration/test_application_approval_flow.py
- [ ] T100 [P] [US4] Unit test for application state transitions in backend/app/tests/unit/test_application_states.py

### Implementation for User Story 4

- [ ] T101 [US4] Implement ApplicationService.submit_application() with validation in backend/app/services/application_service.py
- [ ] T102 [US4] Implement ApplicationService.review_application() with state machine logic in backend/app/services/application_service.py
- [ ] T103 [US4] Implement ApplicationService.get_pending_applications() for SuperAdmin in backend/app/services/application_service.py
- [ ] T104 [US4] Add application state transition validation: DRAFT → PENDING_APPROVAL → APPROVED/REJECTED in backend/app/services/application_service.py
- [ ] T105 [US4] Add email notification for application submitted in backend/app/services/email_notification_service.py
- [ ] T106 [US4] Add email notification for application approved/rejected in backend/app/services/email_notification_service.py
- [ ] T107 [US4] Create email templates for application status updates
- [ ] T108 [US4] Create POST /api/v1/npos/{id}/submit endpoint in backend/app/api/v1/npo_endpoints.py
- [ ] T109 [US4] Create GET /api/v1/admin/npos/applications endpoint with SuperAdmin guard in backend/app/api/v1/admin_endpoints.py
- [ ] T110 [US4] Create POST /api/v1/admin/npos/{id}/applications/{appId}/review endpoint in backend/app/api/v1/admin_endpoints.py
- [ ] T111 [US4] Add SuperAdmin role check middleware in backend/app/middleware/
- [ ] T112 [P] [US4] Create ApplicationStatus component in frontend/augeo-admin/src/features/npo-management/components/ApplicationStatus.tsx
- [ ] T113 [P] [US4] Create application submission button with confirmation dialog
- [ ] T114 [P] [US4] Create SuperAdminReviewPage in frontend/augeo-admin/src/features/npo-management/pages/SuperAdminReviewPage.tsx
- [ ] T115 [US4] Create ApplicationReviewPanel with approve/reject actions in frontend/augeo-admin/src/features/npo-management/components/ApplicationReviewPanel.tsx
- [ ] T116 [US4] Create review notes textarea and required changes checklist
- [ ] T117 [US4] Add routing for SuperAdmin review interface: /admin/npo-applications
- [ ] T118 [US4] Create useApplicationStatus hook in frontend/augeo-admin/src/features/npo-management/hooks/useApplicationStatus.ts

**Checkpoint**: All core user stories complete - NPO creation workflow fully functional end-to-end

---

## Phase 6: User Story 5 - NPO Administrator Accepting Legal Agreements (Priority: P2)

**Goal**: Ensure NPO administrators review and accept EULA/Terms before NPO activation

**Independent Test**: Admin must accept latest legal agreements, acceptance is tracked with IP/timestamp

### Tests for User Story 5 ⚠️

- [ ] T119 [P] [US5] Contract test for GET /api/v1/legal/documents in backend/app/tests/contract/test_legal_endpoints.py
- [ ] T120 [P] [US5] Contract test for POST /api/v1/legal/documents/{id}/accept in backend/app/tests/contract/test_legal_endpoints.py
- [ ] T121 [P] [US5] Integration test for legal agreement acceptance flow in backend/app/tests/integration/test_legal_acceptance_flow.py
- [ ] T122 [P] [US5] Unit test for document versioning logic in backend/app/tests/unit/test_legal_versioning.py

### Implementation for User Story 5

- [ ] T123 [US5] Implement LegalService.get_active_documents() in backend/app/services/legal_service.py
- [ ] T124 [US5] Implement LegalService.accept_document() with IP and user-agent tracking in backend/app/services/legal_service.py
- [ ] T125 [US5] Implement LegalService.check_acceptance_status() for user in backend/app/services/legal_service.py
- [ ] T126 [US5] Add legal agreement check middleware for NPO submission in backend/app/middleware/
- [ ] T127 [US5] Create GET /api/v1/legal/documents endpoint in backend/app/api/v1/legal_endpoints.py
- [ ] T128 [US5] Create POST /api/v1/legal/documents/{id}/accept endpoint in backend/app/api/v1/legal_endpoints.py
- [ ] T129 [US5] Seed initial legal documents (EULA, Terms of Service, Privacy Policy) in backend/seed_legal_documents.py
- [ ] T130 [P] [US5] Create LegalAgreementModal component in frontend/augeo-admin/src/features/npo-management/components/LegalAgreementModal.tsx
- [ ] T131 [P] [US5] Create legal document display with scrollable content and checkbox
- [ ] T132 [US5] Add legal agreement check before NPO submission in frontend
- [ ] T133 [US5] Create acceptance confirmation UI with timestamp display

**Checkpoint**: Legal compliance complete - all user stories independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T134 [P] Add comprehensive API documentation to backend/app/api/v1/openapi.py
- [ ] T135 [P] Create NPO management documentation in docs/features/npo-management.md
- [ ] T136 [P] Add admin user guide for NPO creation workflow
- [ ] T137 [P] Add SuperAdmin guide for application review procedures
- [ ] T138 Code cleanup and refactoring across NPO services
- [ ] T139 Performance optimization: add database query monitoring for NPO endpoints
- [ ] T140 [P] Add unit tests for NPO permission checks in backend/app/tests/unit/test_npo_permissions.py
- [ ] T141 [P] Add unit tests for file upload validation in backend/app/tests/unit/test_file_validation.py
- [ ] T142 [P] Add frontend E2E tests for complete NPO creation in frontend/augeo-admin/tests/e2e/npo-creation.spec.ts
- [ ] T143 [P] Add frontend E2E tests for invitation workflow in frontend/augeo-admin/tests/e2e/invitation-flow.spec.ts
- [ ] T144 Security hardening: review all permission checks and data isolation
- [ ] T145 Add rate limiting for invitation sending to prevent abuse
- [ ] T146 Add monitoring metrics for NPO creation success/failure rates
- [ ] T147 Add audit logging for all SuperAdmin review actions
- [ ] T148 Validate quickstart.md instructions by following setup steps
- [ ] T149 Update main README.md with NPO management feature overview
- [ ] T150 [P] Create NPO management demo data seeding script for testing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
- **Foundational (Phase 1)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 2-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order: US1 → US2 → US3 (MVP) → US4 → US5
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - Independent (NPO creation)
- **User Story 2 (P1)**: Can start after Foundational - Independent (Branding, uses NPO ID from US1 but testable separately)
- **User Story 3 (P1)**: Can start after Foundational - Independent (Invitations, requires approved NPO but testable with mock)
- **User Story 4 (P2)**: Can start after Foundational - Independent (Approval workflow, integrates US1 but testable separately)
- **User Story 5 (P2)**: Can start after Foundational - Independent (Legal agreements, gates US4 but testable separately)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Backend before frontend (API-first)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 0**: T002, T003, T004, T005 can run in parallel
- **Phase 1**: T008-T013 (models), T016-T019 (schemas), T024-T025 (frontend setup) can run in parallel
- **Within each user story**: Test creation tasks can run in parallel
- **User Stories**: US1, US2, US3 can be worked on in parallel by different team members after Phase 1 completes

### MVP Definition

**Minimum Viable Product = Phase 0 + Phase 1 + Phase 2 + Phase 3 + Phase 4 (US1, US2, US3)**

This delivers:
- ✅ NPO creation with full details
- ✅ Branding customization with logo upload
- ✅ Team invitation and collaboration
- ✅ Multi-tenant data isolation
- ✅ Role-based permissions

Can deploy and demo with these 3 user stories. US4 (approval) and US5 (legal) can be added in subsequent releases.

---

## Implementation Strategy

### MVP First (US1 + US2 + US3 Only)

1. Complete Phase 0: Setup
2. Complete Phase 1: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2: User Story 1 (NPO creation)
4. Complete Phase 3: User Story 2 (Branding)
5. Complete Phase 4: User Story 3 (Invitations)
6. **STOP and VALIDATE**: Test all 3 stories independently
7. Deploy MVP to staging for demo

### Full Feature Delivery

1. Complete MVP (US1 + US2 + US3)
2. Add Phase 5: User Story 4 (SuperAdmin approval) → Test independently → Deploy
3. Add Phase 6: User Story 5 (Legal agreements) → Test independently → Deploy
4. Complete Phase 7: Polish and documentation
5. Production deployment with full feature set

### Parallel Team Strategy

With 3 developers:

1. **Week 1**: All developers work on Phase 0 + Phase 1 together
2. **Week 2**: Once Foundational is done:
   - Developer A: User Story 1 (NPO creation)
   - Developer B: User Story 2 (Branding)
   - Developer C: User Story 3 (Invitations)
3. **Week 3**: Integration and testing:
   - Developer A: User Story 4 (Approval workflow)
   - Developer B: User Story 5 (Legal agreements)
   - Developer C: Phase 7 (Polish and testing)
4. Each story completes independently then integrates

---

## Notes

- [P] tasks = different files, no dependencies - safe to parallelize
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- All tests must fail before implementation begins
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Follow existing patterns in backend/app/ for consistency
- Use existing authentication/audit infrastructure
- Azure Blob Storage required for logo uploads (US2)
- Email service required for invitations (US3)
