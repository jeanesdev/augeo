/**
 * Shared TypeScript type definitions for Roles and Permissions
 *
 * These types match the backend API contracts and ensure
 * type safety across frontend applications.
 */

export enum RoleName {
  SUPER_ADMIN = 'Super Admin',
  NPO_ADMIN = 'NPO Admin',
  EVENT_COORDINATOR = 'Event Coordinator',
  STAFF = 'Staff',
  DONOR = 'Donor',
}

export enum PermissionScope {
  PLATFORM = 'platform',
  NPO = 'npo',
  EVENT = 'event',
}

export interface Role {
  id: string;
  name: RoleName;
  description: string;
  hierarchy_level: number;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  scope: PermissionScope;
  resource: string;
  action: string;
  created_at: string;
  updated_at: string;
}

export interface RoleWithPermissions extends Role {
  permissions: Permission[];
}

export interface RoleUpdateRequest {
  role_id: string;
}

export interface PermissionCheck {
  resource: string;
  action: string;
  npo_id?: string | null;
  event_id?: string | null;
}
