import { PasswordResetConfirm } from '@/features/auth/password-reset-confirm'
import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'

const searchSchema = z.object({
  token: z.string().optional(),
})

function PasswordResetConfirmRoute() {
  const { token } = Route.useSearch()
  return <PasswordResetConfirm token={token} />
}

export const Route = createFileRoute('/(auth)/password-reset-confirm')({
  component: PasswordResetConfirmRoute,
  validateSearch: searchSchema,
})
