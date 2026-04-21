'use client'

import { useParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { ChevronLeft, Calendar, Clock, User } from 'lucide-react'
import Link from 'next/link'
import Image from 'next/image'
import GlassCard from '@/components/ui/GlassCard'
import { getBlogPostBySlug, type ContentBlock } from '@/data/blog'

function ContentRenderer({ block }: { block: ContentBlock }) {
  switch (block.type) {
    case 'paragraph':
      return <p className="text-slate-300 leading-relaxed mb-6">{block.text}</p>
    case 'heading':
      return (
        <h2 className="text-xl sm:text-2xl font-bold text-white mt-10 mb-4">
          {block.text}
        </h2>
      )
    case 'code':
      return (
        <div className="mb-6 rounded-xl overflow-hidden border border-white/10">
          <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/10">
            <span className="text-xs text-slate-500 font-mono">{block.language}</span>
          </div>
          <pre className="p-4 overflow-x-auto bg-slate-900/50 text-sm">
            <code className="text-slate-300 font-mono whitespace-pre">{block.code}</code>
          </pre>
        </div>
      )
    case 'list':
      return (
        <ul className="mb-6 space-y-2 pl-1">
          {block.items.map((item, i) => (
            <li key={i} className="flex items-start gap-3 text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 shrink-0 mt-2" />
              <span className="leading-relaxed">{item}</span>
            </li>
          ))}
        </ul>
      )
    case 'quote':
      return (
        <blockquote className="mb-6 border-l-2 border-green-500/40 pl-5 py-1">
          <p className="text-slate-400 italic leading-relaxed">{block.text}</p>
        </blockquote>
      )
    case 'image':
      return (
        <div className="mb-8">
          <div className="rounded-xl overflow-hidden border border-white/10">
            <Image
              src={block.src}
              alt={block.alt}
              width={1000}
              height={600}
              className="w-full h-auto"
              priority
            />
          </div>
          {block.caption && (
            <p className="text-center text-xs text-slate-500 mt-2 italic">{block.caption}</p>
          )}
        </div>
      )
    case 'infobox':
      return (
        <div className={`mb-6 rounded-xl border p-5 ${block.color ?? 'border-blue-500/30 bg-blue-500/5'}`}>
          <div className="flex items-start gap-3">
            {block.icon && <span className="text-2xl shrink-0">{block.icon}</span>}
            <div>
              {block.title && <p className="font-semibold text-white mb-1">{block.title}</p>}
              <p className="text-slate-300 text-sm leading-relaxed">{block.text}</p>
            </div>
          </div>
        </div>
      )
    case 'grid2':
      return (
        <div className="mb-6 grid sm:grid-cols-2 gap-4">
          {block.items.map((item, i) => (
            <div key={i} className="rounded-xl border border-white/10 bg-white/5 p-4">
              {item.icon && <div className="text-2xl mb-2">{item.icon}</div>}
              <p className="text-white font-semibold text-sm mb-1">{item.title}</p>
              <p className="text-slate-400 text-sm leading-relaxed">{item.text}</p>
            </div>
          ))}
        </div>
      )
    case 'steps':
      return (
        <div className="mb-6 space-y-3">
          {block.items.map((item, i) => (
            <div key={i} className="flex gap-4 items-start rounded-xl border border-white/10 bg-white/5 p-4">
              <div className="shrink-0 w-8 h-8 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center text-green-400 font-bold text-sm">
                {i + 1}
              </div>
              <div>
                <p className="text-white font-semibold text-sm mb-0.5">{item.title}</p>
                <p className="text-slate-400 text-sm leading-relaxed">{item.text}</p>
              </div>
            </div>
          ))}
        </div>
      )
    default:
      return null
  }
}

export default function BlogPostPage() {
  const params = useParams()
  const slug = typeof params.slug === 'string' ? params.slug : ''
  const post = getBlogPostBySlug(slug)

  if (!post) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <GlassCard className="p-10 text-center max-w-md">
          <p className="text-4xl mb-4">📝</p>
          <h2 className="text-white font-bold text-xl mb-2">Artikel niet gevonden</h2>
          <p className="text-slate-400 mb-6">Dit blogpost bestaat niet of is verplaatst.</p>
          <Link href="/blog" className="text-green-400 hover:text-green-300 transition-colors text-sm">
            ← Terug naar blog
          </Link>
        </GlassCard>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Back link */}
      <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4 }}>
        <Link href="/blog" className="inline-flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-8 transition-colors">
          <ChevronLeft className="w-4 h-4" />
          Terug naar blog
        </Link>
      </motion.div>

      {/* Hero image */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative h-56 sm:h-72 md:h-80 rounded-2xl overflow-hidden mb-8"
      >
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url('${post.afbeelding}')` }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/40 to-transparent" />
        <div className="absolute bottom-5 left-5 sm:bottom-8 sm:left-8 right-5 sm:right-8">
          <span className={`inline-block text-xs font-semibold px-3 py-1 rounded-full border mb-3 ${post.categorieKleur}`}>
            {post.categorie}
          </span>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white leading-tight">
            {post.titel}
          </h1>
        </div>
      </motion.div>

      {/* Meta + author */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="mb-10"
      >
        <GlassCard className="p-4 sm:p-5">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex items-center gap-3">
              <Image
                src="/profile.jpg"
                alt="Koen Vorsters"
                width={44}
                height={44}
                className="rounded-xl object-cover w-11 h-11"
              />
              <div>
                <p className="text-white font-semibold text-sm">Koen Vorsters</p>
                <p className="text-slate-500 text-xs">Developer & Engineer</p>
              </div>
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-500 sm:ml-auto">
              <span className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" />
                {post.datum}
              </span>
              <span className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                {post.leestijd} leestijd
              </span>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Content */}
      <motion.article
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="mb-12"
      >
        {post.inhoud.map((block, i) => (
          <ContentRenderer key={i} block={block} />
        ))}
      </motion.article>

      {/* Footer CTA */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <GlassCard className="p-6 sm:p-8 text-center">
          <h3 className="text-white font-bold text-lg mb-2">Vond je dit artikel nuttig?</h3>
          <p className="text-slate-400 text-sm mb-5 max-w-md mx-auto">
            Ik schrijf regelmatig over AI, IoT, web development en DevOps. Neem gerust contact op als je vragen hebt.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/blog"
              className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl text-sm font-medium bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-colors"
            >
              Meer artikels
            </Link>
            <a
              href="mailto:koen@vorsters.dev"
              className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:shadow-lg hover:shadow-green-500/25 transition-all"
            >
              Contact opnemen
            </a>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
