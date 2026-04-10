import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Projecten',
  description: 'Ontdek de projecten van Koen Vorsters — van full-stack platforms tot AI agents, IoT pipelines en DevOps infrastructuur.',
}

export default function ProjectenLayout({ children }: { children: React.ReactNode }) {
  return children
}
