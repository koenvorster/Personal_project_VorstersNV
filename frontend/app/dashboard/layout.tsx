import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Tech Playground',
  description: 'Live overzicht van de infrastructuur achter het VorstersNV platform — services, AI agents en tech stack.',
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return children
}
