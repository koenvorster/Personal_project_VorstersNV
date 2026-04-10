import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Over mij',
  description: 'Leer meer over Koen Vorsters — full-stack developer met passie voor AI, IoT en moderne webtechnologieën.',
}

export default function OverMijLayout({ children }: { children: React.ReactNode }) {
  return children
}
