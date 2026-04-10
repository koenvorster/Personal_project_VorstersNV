export default function SkeletonCards() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden animate-pulse"
        >
          <div className="h-48 bg-white/10" />
          <div className="p-5 space-y-3">
            <div className="h-4 bg-white/10 rounded w-3/4" />
            <div className="h-3 bg-white/10 rounded w-full" />
            <div className="h-3 bg-white/10 rounded w-5/6" />
            <div className="flex items-center justify-between pt-3 border-t border-white/5">
              <div className="h-6 bg-white/10 rounded w-16" />
              <div className="h-8 bg-white/10 rounded-xl w-28" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
