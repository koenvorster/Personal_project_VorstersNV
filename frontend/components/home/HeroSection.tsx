'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import Image from 'next/image'
import { MapPin, Mail, ChevronRight, ArrowDown } from 'lucide-react'
import { GithubIcon as Github, LinkedinIcon as Linkedin } from '@/components/icons/BrandIcons'
import GradientButton from '@/components/ui/GradientButton'

export default function HeroSection() {
  return (
    <section className="relative min-h-[100svh] flex items-center justify-center px-4 sm:px-6">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-64 sm:w-96 h-64 sm:h-96 bg-green-600/20 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-52 sm:w-80 h-52 sm:h-80 bg-emerald-600/20 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 w-40 sm:w-64 h-40 sm:h-64 bg-violet-600/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 text-center max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="mx-auto mb-6 sm:mb-8 w-24 h-24 sm:w-28 sm:h-28 rounded-2xl overflow-hidden shadow-2xl shadow-green-500/20 ring-2 ring-green-500/30"
        >
          <Image
            src="/profile.png"
            alt="Koen Vorsters"
            width={112}
            height={112}
            className="w-full h-full object-cover object-top"
            priority
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="inline-flex items-center px-3 sm:px-4 py-1.5 sm:py-2 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs sm:text-sm font-medium mb-4 sm:mb-6">
            <MapPin className="w-3 h-3 sm:w-3.5 sm:h-3.5 mr-1.5" /> België — Beschikbaar voor projecten
          </span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold mb-4 sm:mb-6 leading-[1.1]"
        >
          Hi, ik ben{' '}
          <span className="bg-gradient-to-r from-green-400 via-emerald-400 to-emerald-500 bg-clip-text text-transparent">
            Koen Vorsters
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15 }}
          className="text-xl sm:text-2xl md:text-3xl font-bold text-white/90 mb-4 sm:mb-6"
        >
          Developer · Engineer · Innovator
        </motion.p>

        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-base sm:text-lg md:text-xl text-slate-400 mb-8 sm:mb-10 max-w-2xl mx-auto leading-relaxed px-2"
        >
          Product Engineer met passie voor AI, IoT en full-stack development.
          Ik help bedrijven groeien door slimme digitale oplossingen te bouwen.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-4 sm:px-0"
        >
          <Link href="/over-mij" className="w-full sm:w-auto">
            <GradientButton variant="primary" className="w-full sm:w-auto text-base px-8 py-4 flex items-center justify-center gap-2">
              Over mij <ChevronRight className="w-4 h-4" />
            </GradientButton>
          </Link>
          <Link href="/projecten" className="w-full sm:w-auto">
            <GradientButton variant="outline" className="w-full sm:w-auto text-base px-8 py-4 flex items-center justify-center gap-2">
              Bekijk projecten
            </GradientButton>
          </Link>
          <Link href="/contact" className="w-full sm:w-auto">
            <GradientButton variant="outline" className="w-full sm:w-auto text-base px-8 py-4 flex items-center justify-center gap-2">
              Neem contact op <Mail className="w-4 h-4" />
            </GradientButton>
          </Link>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="flex items-center justify-center gap-4 mt-8 sm:mt-10"
        >
          <a href="https://www.linkedin.com/in/koen-vorsters/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn profiel" className="p-3 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all duration-200">
            <Linkedin className="w-5 h-5" />
          </a>
          <a href="https://github.com/koenvorsters" target="_blank" rel="noopener noreferrer" aria-label="GitHub profiel" className="p-3 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all duration-200">
            <Github className="w-5 h-5" />
          </a>
          <a href="mailto:koen@vorsters.dev" aria-label="Stuur een e-mail" className="p-3 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all duration-200">
            <Mail className="w-5 h-5" />
          </a>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.5 }}
        className="absolute bottom-6 sm:bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
        >
          <ArrowDown className="w-5 h-5 text-slate-500" />
        </motion.div>
      </motion.div>
    </section>
  )
}
