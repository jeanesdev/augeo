# ADR-001: Service-Based Permissions Over Database Permission Table

## Status

**Accepted** - Implemented in Phase 5 (User Story 3)

## Date

2025-10-24

## Context

The original data model specification included a `permissions` table with fine-grained permission records (e.g., "user:create", "user:update", "event:manage") linked to roles. This would require:

1. A `Permission` SQLAlchemy model with fields: id, name, description, scope, resource_type
2. An Alembic migration to create the `permissions` table
3. Seed data for ~20-30 permission records
4. Many-to-many relationship between roles and permissions
5. Permission checking logic that queries the database for role-permission associations

### Problem Statement

During Phase 5 (Role Management) implementation, we needed to decide whether to:
- **Option A**: Implement the full database-backed Permission table as specified
- **Option B**: Use a simpler service-based permission model with hardcoded role logic

### Requirements Context

- **MVP Timeline**: Need to ship authentication/authorization quickly
- **Role Complexity**: Only 5 roles with clear, hierarchical permissions (super_admin > npo_admin > event_coordinator > staff > donor)
- **Permission Stability**: Permissions are tied to business logic and unlikely to change frequently
- **Custom Permissions**: No current requirement for users to define custom permissions
- **Audit Requirements**: Need to log authorization decisions, but not permission changes

## Decision

**We will use service-based permissions (PermissionService) instead of a database Permission table for the MVP.**

Implementation approach:
- `PermissionService` class contains hardcoded permission logic based on roles
- Methods like `can_manage_users()`, `can_assign_roles()`, `can_manage_events()` with role-based conditionals
- Permissions checked at the service layer (e.g., in `UserService.update_role()`)
- No database queries for permission checking - just in-memory logic
- Roles table remains as the source of truth for user roles

### Deferred Tasks

- **T074**: Create Permission model - Not implemented
- **T075**: Create permissions table migration - Not implemented

## Consequences

### Positive

1. **Faster MVP Development**: Eliminates 2 complex tasks (model + migration + seed data)
2. **Simpler Codebase**: No many-to-many relationships, no permission query logic
3. **Better Performance**: No database joins for permission checks - pure Python logic
4. **Easier Testing**: Mock permission checks in service methods, no database fixtures needed
5. **Clear Business Logic**: Permission rules explicit in code, easier to read and understand
6. **Version Control**: Permission changes tracked in git commits, not database migrations

### Negative

1. **Less Flexible**: Adding new permissions requires code changes and deployment
2. **No Admin UI**: Cannot manage permissions through the admin interface
3. **Harder to Audit**: Permission changes are code changes, not database records
4. **Role Coupling**: Permissions tightly coupled to roles, can't mix-and-match
5. **Testing Scope**: Cannot test permission assignment without deploying code
6. **Scalability Concern**: May need refactoring if permission model becomes complex

### Trade-offs

| Aspect | Service-Based (Current) | Database Table (Deferred) |
|--------|------------------------|---------------------------|
| Development Speed | ✅ Fast (2 tasks skipped) | ❌ Slow (model + migration + seed) |
| Runtime Performance | ✅ Fast (no DB queries) | ❌ Slower (joins required) |
| Flexibility | ❌ Code changes needed | ✅ Admin UI possible |
| Auditability | ❌ Git history only | ✅ Database audit trail |
| Testing Complexity | ✅ Simple mocks | ❌ Database fixtures needed |
| Production Changes | ❌ Requires deployment | ✅ Hot-swappable via UI |

## Revisit Criteria

We should reconsider this decision and implement a database Permission table if:

1. **Custom Permissions Needed**: Business requires defining custom permissions per NPO or event
2. **Dynamic Role Creation**: Need to create new roles beyond the 5 standard ones
3. **Permission Combinations**: Need to grant specific permission combinations not tied to roles
4. **Compliance Requirements**: Regulations require database-backed permission audit trail
5. **Admin UI Demand**: Stakeholders need to manage permissions without code deployments
6. **Complex Permission Logic**: Permission rules become too complex for hardcoded conditionals
7. **Multi-Tenancy**: Each NPO needs different permission sets for the same role

### Migration Path

If we need to implement the Permission table later:

1. Create `Permission` model with all fields from data-model.md
2. Create Alembic migration with seed permissions
3. Add `role_permissions` association table
4. Migrate `PermissionService` to query database instead of hardcoded checks
5. Update tests to use permission fixtures
6. Create admin UI for permission management
7. Backfill existing role-permission associations

**Estimated effort**: 5-8 days (T074, T075, refactoring, testing, admin UI)

## References

- **Tasks Deferred**: T074, T075 in `.specify/specs/001-user-authentication-role/tasks.md`
- **Original Spec**: `.specify/specs/001-user-authentication-role/data-model.md` (Permission model)
- **Implementation**: `backend/app/services/permission_service.py`
- **Related ADRs**: None yet

## Notes

This decision was made during Phase 5 implementation after evaluating the actual permission checking needs in the codebase. The simplicity of the 5-role model and clear hierarchical structure made service-based permissions a natural fit for the MVP.

If the platform evolves to support multi-NPO scenarios with varying permission models, or if compliance requires permission change audit trails, revisiting this decision would be warranted.
