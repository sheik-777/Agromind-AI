import { useState, useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import CropDetailModal from '@/components/crops/CropDetailModal'
import { api, type CropListItem, type CropStatsResponse } from '@/services/api'

const PAGE_SIZE = 24

export default function BrowseCrops() {
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [selectedSoil, setSelectedSoil] = useState<string>('')
  const [selectedSeason, setSelectedSeason] = useState<string>('')
  const [sortBy, setSortBy] = useState('name')
  const [page, setPage] = useState(1)
  const [selectedCrop, setSelectedCrop] = useState<CropListItem | null>(null)

  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedSearch(searchQuery)
      setPage(1)
    }, 300)
    return () => clearTimeout(t)
  }, [searchQuery])

  const { data: stats, isFetching: statsLoading } = useQuery<CropStatsResponse, Error>({
    queryKey: ['cropStats'],
    queryFn: () => api.getCropStats(),
    staleTime: 5 * 60 * 1000,
  })

  const { data, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: ['crops', debouncedSearch, selectedSoil, selectedSeason, sortBy, page],
    queryFn: () =>
      api.getCrops({
        page,
        limit: PAGE_SIZE,
        search: debouncedSearch || undefined,
        soil_type: selectedSoil || undefined,
        season: selectedSeason || undefined,
        sort: sortBy,
        order: 'asc',
      }),
    retry: 1,
  })

  const total = data?.total ?? 0
  const totalPages = data?.total_pages ?? 1
  const from = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1
  const to = Math.min(page * PAGE_SIZE, total)

  const commonSoils = useMemo(() => {
    if (!stats?.soil_types) return []
    return stats.soil_types.slice(0, 8).map((s) => s.name)
  }, [stats])

  const commonSeasons = useMemo(() => {
    if (!stats?.seasons) return []
    return stats.seasons.slice(0, 8).map((s) => s.name)
  }, [stats])

  const goToPage = (p: number) => {
    if (p < 1 || p > totalPages) return
    setPage(p)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  if (isLoading && !data) {
    return (
      <div className="min-h-screen py-8 lg:py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold font-display text-neutral-900 dark:text-white mb-4">Browse Crops</h1>
          <p className="text-lg text-neutral-600 dark:text-neutral-400">Loading crop dataset…</p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-6 animate-pulse">
              <div className="w-10 h-10 rounded-lg bg-neutral-200 dark:bg-neutral-700 mb-4" />
              <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-2/3 mb-2" />
              <div className="h-3 bg-neutral-100 dark:bg-neutral-800 rounded w-1/2 mb-4" />
              <div className="space-y-2">
                <div className="h-3 bg-neutral-100 dark:bg-neutral-800 rounded" />
                <div className="h-3 bg-neutral-100 dark:bg-neutral-800 rounded" />
                <div className="h-3 bg-neutral-100 dark:bg-neutral-800 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-8 lg:py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10"
      >
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight font-display text-neutral-900 dark:text-white mb-4">
          Browse Crops
        </h1>
        <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto">
          Explore AgroMind's complete crop knowledge database with growth requirements and field compatibility.
        </p>
        {!statsLoading && stats && (
          <p className="mt-3 text-sm text-neutral-500 dark:text-neutral-400">
            {stats.total_records.toLocaleString()} crop records · {stats.unique_crops.toLocaleString()} unique crops
          </p>
        )}
      </motion.div>

      {/* Search */}
      <div className="max-w-md mx-auto mb-6">
        <div className="relative">
          <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search crops (e.g. rice, wheat, tomato)…"
            className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-900 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder-neutral-400 focus:border-forest-500 focus:ring-2 focus:ring-forest-500/20 focus:outline-none transition-all"
          />
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-5xl mx-auto mb-6 flex flex-wrap items-center justify-center gap-3">
        <select
          value={selectedSoil}
          onChange={(e) => { setSelectedSoil(e.target.value); setPage(1) }}
          className="px-4 py-2 rounded-xl text-sm font-medium bg-white dark:bg-neutral-900 border-2 border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 focus:border-forest-500 focus:outline-none"
        >
          <option value="">All soil types</option>
          {commonSoils.map((s) => (
            <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
          ))}
        </select>

        <select
          value={selectedSeason}
          onChange={(e) => { setSelectedSeason(e.target.value); setPage(1) }}
          className="px-4 py-2 rounded-xl text-sm font-medium bg-white dark:bg-neutral-900 border-2 border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 focus:border-forest-500 focus:outline-none"
        >
          <option value="">All seasons</option>
          {commonSeasons.map((s) => (
            <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
          ))}
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-4 py-2 rounded-xl text-sm font-medium bg-white dark:bg-neutral-900 border-2 border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 focus:border-forest-500 focus:outline-none"
        >
          <option value="name">Sort: Name</option>
          <option value="soil_type">Sort: Soil type</option>
          <option value="season">Sort: Season</option>
          <option value="ph">Sort: pH</option>
          <option value="temp">Sort: Temperature</option>
        </select>

        {(selectedSoil || selectedSeason || debouncedSearch) && (
          <button
            onClick={() => { setSelectedSoil(''); setSelectedSeason(''); setSearchQuery(''); setSortBy('name'); setPage(1) }}
            className="px-4 py-2 rounded-xl text-sm font-medium text-forest-600 dark:text-forest-400 hover:bg-forest-50 dark:hover:bg-forest-950/40 transition-colors"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Count */}
      <div className="max-w-5xl mx-auto mb-4 text-sm text-neutral-500 dark:text-neutral-400">
        {isFetching ? 'Updating…' : (
          total > 0 ? `Showing ${from}–${to} of ${total.toLocaleString()} crops` : 'No crops match your filters'
        )}
      </div>

      {isError && (
        <div className="max-w-5xl mx-auto mb-6">
          <div className="rounded-xl border-2 border-red-100 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 p-4 text-sm text-red-600 dark:text-red-400 flex items-center justify-between">
            <span>Could not load crops from the backend. Is the server running?</span>
            <button onClick={() => refetch()} className="px-3 py-1 rounded-lg bg-red-600 text-white text-xs font-medium">Retry</button>
          </div>
        </div>
      )}

      {/* Crop Grid */}
      <div className="max-w-5xl mx-auto grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {(data?.crops ?? []).map((crop) => (
          <button
            key={`${crop.id}-${crop.name}`}
            onClick={() => setSelectedCrop(crop)}
            className="text-left h-full"
          >
            <Card variant="glass" className="p-5 h-full cursor-pointer">
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-lg font-bold text-neutral-900 dark:text-white">{crop.name}</h3>
              </div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                <Badge variant="primary" size="sm">{crop.season.replace(/_/g, ' ')}</Badge>
                <Badge variant="accent" size="sm">{crop.soil_type.replace(/_/g, ' ')}</Badge>
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">pH range</span>
                  <span className="font-medium text-neutral-700 dark:text-neutral-300">
                    {crop.ph_min.toFixed(1)} – {crop.ph_max.toFixed(1)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Temperature</span>
                  <span className="font-medium text-neutral-700 dark:text-neutral-300">
                    {crop.temp_min.toFixed(0)}–{crop.temp_max.toFixed(0)}°C
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Rainfall</span>
                  <span className="font-medium text-neutral-700 dark:text-neutral-300">
                    {crop.rain_min.toFixed(0)}–{crop.rain_max.toFixed(0)} mm
                  </span>
                </div>
              </div>
              <div className="mt-3 text-xs font-medium text-forest-600 dark:text-forest-400 flex items-center gap-1">
                View details
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Card>
          </button>
        ))}
      </div>

      {/* Empty state */}
      {!isLoading && data && data.crops.length === 0 && (
        <div className="text-center py-16">
          <span className="text-6xl mb-4 block">🌾</span>
          <h3 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">No crops found</h3>
          <p className="text-neutral-500 dark:text-neutral-400">Try adjusting your search or filter criteria.</p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="max-w-5xl mx-auto mt-8 flex flex-wrap items-center justify-center gap-2">
          <button
            onClick={() => goToPage(page - 1)}
            disabled={page <= 1}
            className="px-4 py-2 rounded-xl text-sm font-medium bg-white dark:bg-neutral-900 border-2 border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none"
          >
            ← Prev
          </button>

          <span className="px-3 py-2 text-sm text-neutral-600 dark:text-neutral-400">
            Page {page} of {totalPages}
          </span>

          <button
            onClick={() => goToPage(page + 1)}
            disabled={page >= totalPages}
            className="px-4 py-2 rounded-xl text-sm font-medium bg-white dark:bg-neutral-900 border-2 border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none"
          >
            Next →
          </button>
        </div>
      )}

      <AnimatePresence>
        {selectedCrop && (
          <CropDetailModal crop={selectedCrop} onClose={() => setSelectedCrop(null)} />
        )}
      </AnimatePresence>
    </div>
  )
}