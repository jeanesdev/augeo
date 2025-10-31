import type { User as ApiUser } from '../api/users-api'
import { RoleAssignmentDialog } from './role-assignment-dialog'
import { UsersActionDialog } from './users-action-dialog'
import { UsersDeleteDialog } from './users-delete-dialog'
import { UsersInviteDialog } from './users-invite-dialog'
import { useUsers } from './users-provider'
import { UsersResetPasswordDialog } from './users-reset-password-dialog'

export function UsersDialogs() {
  const { open, setOpen, currentRow, setCurrentRow } = useUsers()

  // Convert schema User to API User for RoleAssignmentDialog
  const apiUser: ApiUser | null = currentRow
    ? {
        id: currentRow.id,
        email: currentRow.email,
        first_name: currentRow.first_name,
        last_name: currentRow.last_name,
        phone: currentRow.phone,
        role: currentRow.role,
        npo_id: currentRow.npo_id,
        email_verified: currentRow.email_verified,
        is_active: currentRow.is_active,
        last_login_at: currentRow.last_login_at,
        created_at: currentRow.created_at,
        updated_at: currentRow.updated_at,
      }
    : null

  return (
    <>
      <UsersActionDialog
        key='user-add'
        open={open === 'add'}
        onOpenChange={() => setOpen('add')}
      />

      <UsersInviteDialog
        key='user-invite'
        open={open === 'invite'}
        onOpenChange={() => setOpen('invite')}
      />

      {currentRow && (
        <>
          <UsersActionDialog
            key={`user-edit-${currentRow.id}`}
            open={open === 'edit'}
            onOpenChange={() => {
              setOpen('edit')
              setTimeout(() => {
                setCurrentRow(null)
              }, 500)
            }}
            currentRow={currentRow}
          />

          <RoleAssignmentDialog
            key={`user-role-${currentRow.id}`}
            user={apiUser}
            open={open === 'role'}
            onOpenChange={() => {
              setOpen('role')
              setTimeout(() => {
                setCurrentRow(null)
              }, 500)
            }}
          />

          <UsersResetPasswordDialog
            key={`user-reset-${currentRow.id}`}
            open={open === 'resetPassword'}
            onOpenChange={() => {
              setOpen('resetPassword')
              setTimeout(() => {
                setCurrentRow(null)
              }, 500)
            }}
            currentRow={currentRow}
          />

          <UsersDeleteDialog
            key={`user-delete-${currentRow.id}`}
            open={open === 'delete'}
            onOpenChange={() => {
              setOpen('delete')
              setTimeout(() => {
                setCurrentRow(null)
              }, 500)
            }}
            currentRow={currentRow}
          />
        </>
      )}
    </>
  )
}
