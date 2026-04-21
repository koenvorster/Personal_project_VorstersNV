import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Dashboard — Koen Vorsters',
  description: 'Persoonlijk dashboard: live overzicht van infrastructuur, AI agents en platformstatus.',
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return children
}
