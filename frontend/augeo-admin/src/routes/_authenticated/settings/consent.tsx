import { ConsentSettingsPage } from '@/pages/legal'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/settings/consent')({
  component: ConsentSettingsPage,
})
