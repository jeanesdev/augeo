"""User management endpoints for administrators."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.users import (
    RoleUpdateRequest,
    UserActivateRequest,
    UserCreateRequest,
    UserListResponse,
    UserPublicWithRole,
    UserUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    role: str | None = None,
    npo_id: uuid.UUID | None = None,
    email_verified: bool | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """List users with pagination and filtering.

    Access Control:
    - Super Admin: Can view all users
    - NPO Admin: Can view users in their NPO
    - Event Coordinator: Can view users in their NPO
    - Staff/Donor: Not allowed

    Query Parameters:
    - page: Page number (1-indexed)
    - per_page: Items per page (1-100, default 20)
    - role: Filter by role name
    - npo_id: Filter by NPO ID
    - email_verified: Filter by email verification status
    - is_active: Filter by active status
    - search: Search in name and email

    Returns:
        Paginated list of users with role information

    Raises:
        400: Invalid pagination parameters
        403: Insufficient permissions
    """
    user_service = UserService()

    try:
        return await user_service.list_users(
            db=db,
            current_user=current_user,
            page=page,
            per_page=per_page,
            role=role,
            npo_id=npo_id,
            email_verified=email_verified,
            is_active=is_active,
            search=search,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserPublicWithRole)
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new user (admin only).

    Access Control:
    - Super Admin: Can create users with any role in any NPO
    - NPO Admin: Can create users in their NPO (except super_admin)
    - Others: Not allowed

    Business Rules:
    - Email must be unique
    - npo_admin and event_coordinator roles MUST have npo_id
    - staff and donor roles MUST NOT have npo_id
    - Created user gets temporary password (should be changed on first login)
    - User starts with email_verified=false, is_active=false

    Args:
        user_data: User creation data

    Returns:
        Created user with role information

    Raises:
        400: Invalid data or role/npo_id constraint violation
        403: Insufficient permissions
        409: Email already exists
    """
    user_service = UserService()

    try:
        user = await user_service.create_user(
            db=db, current_user=current_user, user_data=user_data
        )

        # Get role name for response
        from sqlalchemy import select

        from app.models.base import Base

        roles_table = Base.metadata.tables["roles"]
        role_stmt = select(roles_table.c.name).where(roles_table.c.id == user.role_id)
        role_result = await db.execute(role_stmt)
        role_name = role_result.scalar_one()

        # Log user creation
        audit_service = AuditService()
        audit_service.log_info(
            f"User created: {user.email} with role {role_name}",
            extra={
                "event": "USER_CREATED",
                "user_id": str(current_user.id),
                "target_user_id": str(user.id),
                "role": role_name,
                "npo_id": str(user.npo_id) if user.npo_id else None,
            },
        )

        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "role": role_name,
            "npo_id": user.npo_id,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
    except ValueError as e:
        if "already exists" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{user_id}", response_model=UserPublicWithRole)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a user by ID.

    Access Control:
    - Super Admin: Can view any user
    - NPO Admin: Can view users in their NPO
    - Event Coordinator: Can view users in their NPO
    - Others: Not allowed

    Args:
        user_id: User ID

    Returns:
        User with role information

    Raises:
        403: Insufficient permissions
        404: User not found
    """
    user_service = UserService()

    try:
        user = await user_service.get_user(db=db, current_user=current_user, user_id=user_id)

        # Get role name
        from sqlalchemy import select

        from app.models.base import Base

        roles_table = Base.metadata.tables["roles"]
        role_stmt = select(roles_table.c.name).where(roles_table.c.id == user.role_id)
        role_result = await db.execute(role_stmt)
        role_name = role_result.scalar_one()

        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "role": role_name,
            "npo_id": user.npo_id,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/{user_id}", response_model=UserPublicWithRole)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update user profile.

    Access Control:
    - Super Admin: Can update any user
    - NPO Admin: Can update users in their NPO
    - Others: Not allowed

    Args:
        user_id: User ID
        user_data: Updated user data

    Returns:
        Updated user with role information

    Raises:
        403: Insufficient permissions
        404: User not found
    """
    user_service = UserService()

    try:
        user = await user_service.update_user(
            db=db, current_user=current_user, user_id=user_id, user_data=user_data
        )

        # Get role name
        from sqlalchemy import select

        from app.models.base import Base

        roles_table = Base.metadata.tables["roles"]
        role_stmt = select(roles_table.c.name).where(roles_table.c.id == user.role_id)
        role_result = await db.execute(role_stmt)
        role_name = role_result.scalar_one()

        # Log user update
        audit_service = AuditService()
        audit_service.log_info(
            f"User updated: {user.email}",
            extra={
                "event": "USER_UPDATED",
                "user_id": str(current_user.id),
                "target_user_id": str(user.id),
            },
        )

        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "role": role_name,
            "npo_id": user.npo_id,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a user (soft delete by deactivating).

    Access Control:
    - Super Admin: Can delete any user
    - NPO Admin: Can delete users in their NPO
    - Others: Not allowed

    Args:
        user_id: User ID

    Raises:
        403: Insufficient permissions
        404: User not found
    """
    user_service = UserService()

    try:
        user = await user_service.deactivate_user(
            db=db, current_user=current_user, user_id=user_id
        )

        # Log user deletion
        audit_service = AuditService()
        audit_service.log_info(
            f"User deactivated: {user.email}",
            extra={
                "event": "USER_DELETED",
                "user_id": str(current_user.id),
                "target_user_id": str(user.id),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/{user_id}/role", response_model=UserPublicWithRole)
async def update_user_role(
    user_id: uuid.UUID,
    role_data: RoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update user's role and optionally npo_id.

    Access Control:
    - Super Admin: Can assign any role
    - NPO Admin: Can assign roles except super_admin
    - Event Coordinator: Can assign staff and donor only
    - Others: Not allowed

    Business Rules:
    - npo_admin and event_coordinator roles MUST have npo_id
    - staff and donor roles MUST NOT have npo_id
    - Changing from npo_admin/event_coordinator to staff/donor clears npo_id

    Args:
        user_id: User ID
        role_data: New role and optional npo_id

    Returns:
        Updated user with role information

    Raises:
        400: Invalid role/npo_id combination
        403: Insufficient permissions
        404: User not found
    """
    user_service = UserService()

    try:
        user = await user_service.update_role(
            db=db,
            current_user=current_user,
            user_id=user_id,
            role=role_data.role,
            npo_id=role_data.npo_id,
        )

        # Get role name
        from sqlalchemy import select

        from app.models.base import Base

        roles_table = Base.metadata.tables["roles"]
        role_stmt = select(roles_table.c.name).where(roles_table.c.id == user.role_id)
        role_result = await db.execute(role_stmt)
        role_name = role_result.scalar_one()

        # Log role change
        audit_service = AuditService()
        audit_service.log_info(
            f"User role changed: {user.email} -> {role_name}",
            extra={
                "event": "ROLE_CHANGED",
                "user_id": str(current_user.id),
                "target_user_id": str(user.id),
                "new_role": role_name,
                "npo_id": str(user.npo_id) if user.npo_id else None,
            },
        )

        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "role": role_name,
            "npo_id": user.npo_id,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{user_id}/activate", response_model=UserPublicWithRole)
async def activate_user(
    user_id: uuid.UUID,
    activate_data: UserActivateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Activate or deactivate a user account.

    Access Control:
    - Super Admin: Can activate/deactivate any user
    - NPO Admin: Can activate/deactivate users in their NPO
    - Others: Not allowed

    Args:
        user_id: User ID
        activate_data: Activation status

    Returns:
        Updated user with role information

    Raises:
        403: Insufficient permissions
        404: User not found
    """
    user_service = UserService()

    try:
        if activate_data.is_active:
            user = await user_service.activate_user(
                db=db, current_user=current_user, user_id=user_id
            )
            action = "activated"
        else:
            user = await user_service.deactivate_user(
                db=db, current_user=current_user, user_id=user_id
            )
            action = "deactivated"

        # Get role name
        from sqlalchemy import select

        from app.models.base import Base

        roles_table = Base.metadata.tables["roles"]
        role_stmt = select(roles_table.c.name).where(roles_table.c.id == user.role_id)
        role_result = await db.execute(role_stmt)
        role_name = role_result.scalar_one()

        # Log activation change
        audit_service = AuditService()
        audit_service.log_info(
            f"User {action}: {user.email}",
            extra={
                "event": "USER_ACTIVATION_CHANGED",
                "user_id": str(current_user.id),
                "target_user_id": str(user.id),
                "is_active": user.is_active,
            },
        )

        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "role": role_name,
            "npo_id": user.npo_id,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
