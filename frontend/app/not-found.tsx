import Link from 'next/link'
import { Home } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <p className="text-8xl font-extrabold text-white/10 mb-4">404</p>
        <h1 className="text-2xl font-bold text-white mb-3">Pagina niet gevonden</h1>
        <p className="text-slate-400 mb-8">
          De pagina die je zoekt bestaat niet of is verplaatst.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:shadow-lg hover:shadow-green-500/25 transition-all"
        >
          <Home className="w-4 h-4" />
          Terug naar home
        </Link>
      </div>
    </div>
  )
}
