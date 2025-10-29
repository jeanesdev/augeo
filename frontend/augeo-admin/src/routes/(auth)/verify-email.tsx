import { EmailVerificationPage } from '@/features/auth/email-verification'
import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'

const searchSchema = z.object({
  token: z.string().optional(),
  email: z.string().optional(),
})

function VerifyEmailRoute() {
  const { token, email } = Route.useSearch()
  return <EmailVerificationPage token={token} email={email} />
}

export const Route = createFileRoute('/(auth)/verify-email')({
  component: VerifyEmailRoute,
  validateSearch: searchSchema,
})
