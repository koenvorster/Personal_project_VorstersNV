import Link from 'next/link'
import { MapPin, Mail } from 'lucide-react'
import { GithubIcon, LinkedinIcon } from '@/components/icons/BrandIcons'

export default function Footer() {
  return (
    <footer className="bg-slate-950 mt-16 sm:mt-20">
      <div className="h-px bg-gradient-to-r from-transparent via-green-500 to-transparent" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* Brand */}
          <div className="sm:col-span-2 lg:col-span-1">
            <span className="text-xl font-bold bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">
              Koen Vorsters
            </span>
            <p className="mt-3 text-slate-400 text-sm leading-relaxed max-w-xs">
              Full-stack developer met passie voor AI, IoT en moderne webtechnologieën.
              Ik bouw slimme oplossingen die hardware en software samenbrengen.
            </p>
            <div className="mt-4 flex flex-col gap-1.5">
              <div className="flex items-center space-x-2 text-sm text-slate-500">
                <MapPin className="w-3.5 h-3.5" />
                <span>België</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-slate-500">
                <Mail className="w-3.5 h-3.5" />
                <a href="mailto:koen@vorsters.dev" className="hover:text-white transition-colors">koen@vorsters.dev</a>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3">
              <a href="https://www.linkedin.com/in/koen-vorsters/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn profiel" className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all">
                <LinkedinIcon className="w-4 h-4" />
              </a>
              <a href="https://github.com/koenvorsters" target="_blank" rel="noopener noreferrer" aria-label="GitHub profiel" className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all">
                <GithubIcon className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Navigation */}
          <div>
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Navigatie</h3>
            <ul className="space-y-2">
              {[
                { href: '/', label: 'Home' },
                { href: '/projecten', label: 'Projecten' },
                { href: '/over-mij', label: 'Over mij' },
                { href: '/blog', label: 'Blog' },
                { href: '/dashboard', label: 'Dashboard' },
              ].map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="text-slate-400 hover:text-white text-sm transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Contact</h3>
            <ul className="space-y-2">
              <li>
                <a href="mailto:koen@vorsters.dev" className="text-slate-400 hover:text-white text-sm transition-colors">
                  koen@vorsters.dev
                </a>
              </li>
              <li>
                <a href="https://www.linkedin.com/in/koen-vorsters/" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-white text-sm transition-colors">
                  LinkedIn
                </a>
              </li>
              <li>
                <a href="https://github.com/koenvorsters" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-white text-sm transition-colors">
                  GitHub
                </a>
              </li>
            </ul>
            <div className="mt-6">
              <Link href="/login" className="text-slate-600 hover:text-slate-400 text-xs transition-colors">
                Admin →
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-8 sm:mt-10 pt-6 sm:pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-4">
          <p className="text-slate-500 text-xs sm:text-sm">
            © {new Date().getFullYear()} Koen Vorsters. Alle rechten voorbehouden.
          </p>
          <p className="text-slate-600 text-xs">
            Gebouwd met Next.js, FastAPI & Tailwind CSS
          </p>
        </div>
      </div>
    </footer>
  )
}
