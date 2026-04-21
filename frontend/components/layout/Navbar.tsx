'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, Code2, ShoppingCart, LogOut, LogIn, LayoutDashboard, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useCartStore } from '@/lib/cartStore'
import { useSession, signIn, signOut } from 'next-auth/react'

const publicLinks = [
  { href: '/', label: 'Home' },
  { href: '/projecten', label: 'Projecten' },
  { href: '/diensten', label: 'Diensten' },
  { href: '/ai-lab', label: 'AI Lab' },
  { href: '/blog', label: 'Blog' },
  { href: '/how-tos', label: "How-to's" },
  { href: '/uses', label: 'Uses' },
  { href: '/contact', label: 'Contact' },
]

const adminLinks = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/shop', label: 'Shop', icon: null },
]

export default function Navbar() {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)
  const { data: session, status } = useSession()
  const cartCount = useCartStore((s) => s.items.reduce((sum, i) => sum + i.aantal, 0))

  const isAdmin = session?.user?.rol === 'admin' || session?.user?.rol === 'tester'
  const visibleLinks = [...publicLinks, ...(isAdmin ? adminLinks : [])]

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href)

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2 group">
            <div className="bg-gradient-to-br from-green-500 to-emerald-600 p-2 rounded-xl group-hover:scale-105 transition-transform shadow-lg shadow-green-500/20">
              <Code2 className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg sm:text-xl md:text-2xl font-extrabold tracking-tight text-white group-hover:text-green-400 transition-colors">
              Koen<span className="text-green-500"> Vorsters</span>
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center space-x-1">
            {publicLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                aria-current={isActive(link.href) ? 'page' : undefined}
                className={cn(
                  'px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                  isActive(link.href)
                    ? 'bg-green-500/20 text-green-400'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                )}
              >
                {link.label}
              </Link>
            ))}

            {/* Admin links */}
            {isAdmin && adminLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                aria-current={isActive(link.href) ? 'page' : undefined}
                className={cn(
                  'px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-1.5',
                  isActive(link.href)
                    ? 'bg-violet-500/20 text-violet-400'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                )}
              >
                {link.icon && <link.icon className="w-3.5 h-3.5" />}
                {link.label}
              </Link>
            ))}

            {/* Cart */}
            <Link
              href="/winkelwagen"
              aria-label="Winkelwagen"
              className="relative ml-1 p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            >
              <ShoppingCart className="w-5 h-5" />
              {cartCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[1.1rem] h-[1.1rem] flex items-center justify-center text-[10px] font-bold bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-full px-1">
                  {cartCount}
                </span>
              )}
            </Link>

            {/* Auth area */}
            {status === 'loading' ? (
              <div className="ml-1 w-8 h-8 rounded-full bg-white/5 animate-pulse" />
            ) : session ? (
              <div className="ml-2 flex items-center gap-2">
                <Link href="/dashboard" className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                    <User className="w-3.5 h-3.5 text-white" />
                  </div>
                  <span className="text-sm text-white font-medium max-w-[100px] truncate">
                    {session.user?.name?.split(' ')[0] ?? 'Koen'}
                  </span>
                  <span className={cn(
                    'text-[10px] px-1.5 py-0.5 rounded-full font-medium',
                    session.user?.rol === 'admin' ? 'bg-violet-500/20 text-violet-400' :
                    session.user?.rol === 'tester' ? 'bg-blue-500/20 text-blue-400' :
                    'bg-slate-500/20 text-slate-400'
                  )}>
                    {session.user?.rol ?? 'viewer'}
                  </span>
                </Link>
                <button
                  onClick={() => signOut({ callbackUrl: '/' })}
                  className="p-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-400/10 transition-colors"
                  aria-label="Uitloggen"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => signIn('keycloak', { callbackUrl: '/dashboard' })}
                className="ml-2 flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
              >
                <LogIn className="w-4 h-4" />
                Login
              </button>
            )}
          </div>

          {/* Mobile: cart + hamburger */}
          <div className="md:hidden flex items-center gap-1">
            <Link
              href="/winkelwagen"
              aria-label="Winkelwagen"
              className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            >
              <ShoppingCart className="w-5 h-5" />
              {cartCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[1.1rem] h-[1.1rem] flex items-center justify-center text-[10px] font-bold bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-full px-1">
                  {cartCount}
                </span>
              )}
            </Link>
            <button
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label={mobileOpen ? 'Menu sluiten' : 'Menu openen'}
              aria-expanded={mobileOpen}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden border-t border-white/10 bg-slate-950/95 overflow-hidden"
          >
            <div className="px-4 py-4 space-y-1">
              {visibleLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    'block px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200',
                    isActive(link.href)
                      ? 'bg-green-500/20 text-green-400'
                      : 'text-slate-400 hover:text-white hover:bg-white/5'
                  )}
                  aria-current={isActive(link.href) ? 'page' : undefined}
                >
                  {link.label}
                </Link>
              ))}
              <div className="pt-2 border-t border-white/10">
                {session ? (
                  <div className="space-y-1">
                    <div className="px-4 py-2 flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                        <User className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <p className="text-white text-sm font-medium">{session.user?.name ?? 'Koen'}</p>
                        <p className="text-slate-500 text-xs">{session.user?.rol ?? 'viewer'}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => { setMobileOpen(false); signOut({ callbackUrl: '/' }) }}
                      className="w-full flex items-center gap-2 px-4 py-3 rounded-lg text-sm font-medium text-red-400 hover:bg-red-400/10 transition-colors"
                    >
                      <LogOut className="w-4 h-4" /> Uitloggen
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => { setMobileOpen(false); signIn('keycloak', { callbackUrl: '/dashboard' }) }}
                    className="w-full flex items-center gap-2 px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
                  >
                    <LogIn className="w-4 h-4" /> Aanmelden met Keycloak
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}
