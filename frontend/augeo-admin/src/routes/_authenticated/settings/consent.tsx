import { createFileRoute } from '@tanstack/react-router'
import { ConsentSettingsPage } from '@/pages/legal'

export const Route = createFileRoute('/_authenticated/settings/consent')({
  component: ConsentSettingsPage,
})
