"""Permission service for role-based access control.

This service provides methods to check if a user can perform specific actions
based on their role and NPO assignment.

Role hierarchy:
- super_admin: Full platform access across all NPOs
- npo_admin: Full access within assigned NPO(s)
- event_coordinator: Event/auction management within NPO
- staff: Donor registration/check-in within assigned events
- donor: Bidding and profile management only
"""

import uuid
from typing import Any


class PermissionService:
    """Service for checking user permissions based on roles."""

    # Roles that require npo_id
    ROLES_REQUIRING_NPO = {"npo_admin", "event_coordinator"}

    # Roles that forbid npo_id
    ROLES_FORBIDDING_NPO = {"donor", "staff"}

    # Roles that can view users
    ROLES_CAN_VIEW_USERS = {"super_admin", "npo_admin", "event_coordinator"}

    # Roles that can create users
    ROLES_CAN_CREATE_USERS = {"super_admin", "npo_admin", "event_coordinator"}

    # Roles that can assign roles
    ROLES_CAN_ASSIGN_ROLES = {"super_admin", "npo_admin", "event_coordinator"}

    def can_view_user(self, user: Any, target_user_npo_id: uuid.UUID | None) -> bool:
        """Check if user can view a target user.

        Args:
            user: User making the request (must have .role and .npo_id attributes)
            target_user_npo_id: NPO ID of the user being viewed (None for platform-wide users)

        Returns:
            True if user can view the target user, False otherwise

        Rules:
            - super_admin: Can view all users
            - npo_admin: Can view users in their NPO only
            - event_coordinator: Can view users in their NPO only
            - staff/donor: Cannot view user lists
        """
        if user.role_name not in self.ROLES_CAN_VIEW_USERS:
            return False

        if user.role_name == "super_admin":
            return True

        # NPO admin and event coordinator can only view users in their NPO
        if user.role_name in {"npo_admin", "event_coordinator"}:
            if user.npo_id is None:
                return False
            return bool(target_user_npo_id == user.npo_id)

        return False

    def can_create_user(self, user: Any, target_npo_id: uuid.UUID | None) -> bool:
        """Check if user can create a new user.

        Args:
            user: User making the request
            target_npo_id: NPO ID for the new user (None for platform-wide users like donors)

        Returns:
            True if user can create a user with the specified NPO, False otherwise

        Rules:
            - super_admin: Can create users in any NPO
            - npo_admin: Can create users in their NPO only (including donors)
            - event_coordinator: Can create users in their NPO only (staff/donors for events)
            - Others: Cannot create users
        """
        if user.role_name not in self.ROLES_CAN_CREATE_USERS:
            return False

        if user.role_name == "super_admin":
            return True

        # NPO admin can create users in their NPO or without NPO (donors)
        if user.role_name == "npo_admin":
            if user.npo_id is None:
                return False
            # Can create users with no NPO (donors) or users in their NPO
            return target_npo_id is None or target_npo_id == user.npo_id

        # Event coordinator can create users in their NPO only
        if user.role_name == "event_coordinator":
            if user.npo_id is None:
                return False
            return bool(target_npo_id == user.npo_id)

        return False

    def can_assign_role(self, user: Any, target_role: str) -> bool:
        """Check if user can assign a specific role.

        Args:
            user: User making the request
            target_role: Role being assigned

        Returns:
            True if user can assign this role, False otherwise

        Rules:
            - super_admin: Can assign any role
            - npo_admin: Can assign all roles except super_admin
            - event_coordinator: Can assign staff and donor only
            - Others: Cannot assign roles
        """
        if user.role_name not in self.ROLES_CAN_ASSIGN_ROLES:
            return False

        if user.role_name == "super_admin":
            return True

        if user.role_name == "npo_admin":
            # NPO admin cannot assign super_admin role
            return target_role != "super_admin"

        if user.role_name == "event_coordinator":
            # Event coordinator can only assign staff and donor
            return target_role in {"staff", "donor"}

        return False

    def can_modify_user(self, user: Any, target_user_npo_id: uuid.UUID | None) -> bool:
        """Check if user can modify (update/delete) a target user.

        Args:
            user: User making the request
            target_user_npo_id: NPO ID of the user being modified

        Returns:
            True if user can modify the target user, False otherwise

        Rules:
            - super_admin: Can modify all users
            - npo_admin: Can modify users in their NPO only
            - Others: Cannot modify users
        """
        if user.role_name == "super_admin":
            return True

        if user.role_name == "npo_admin":
            if user.npo_id is None:
                return False
            # Can modify users in their NPO or users without NPO (donors)
            return target_user_npo_id is None or target_user_npo_id == user.npo_id

        return False

    def role_requires_npo_id(self, role: str) -> bool:
        """Check if a role requires npo_id to be set.

        Args:
            role: Role name

        Returns:
            True if role requires npo_id, False otherwise
        """
        return role in self.ROLES_REQUIRING_NPO

    def role_forbids_npo_id(self, role: str) -> bool:
        """Check if a role forbids npo_id from being set.

        Args:
            role: Role name

        Returns:
            True if role forbids npo_id, False otherwise
        """
        return role in self.ROLES_FORBIDDING_NPO

    def validate_role_npo_id_combination(
        self, role: str, npo_id: uuid.UUID | None
    ) -> tuple[bool, str | None]:
        """Validate that role and npo_id combination is valid.

        Args:
            role: Role name
            npo_id: NPO ID (can be None)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.role_requires_npo_id(role) and npo_id is None:
            return False, f"Role '{role}' requires npo_id to be set"

        if self.role_forbids_npo_id(role) and npo_id is not None:
            return False, f"Role '{role}' must not have npo_id set"

        return True, None
