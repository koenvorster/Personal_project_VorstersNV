import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Blog',
  description: 'Technische tutorials, inzichten en tips over AI, IoT, web development en DevOps door Koen Vorsters.',
}

export default function BlogLayout({ children }: { children: React.ReactNode }) {
  return children
}
