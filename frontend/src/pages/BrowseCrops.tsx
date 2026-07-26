import { useState } from 'react'
import { motion } from 'framer-motion'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'

const crops = [
  { name: 'Rice', emoji: '🌾', score: 92, season: 'Kharif', soilType: 'Loamy', water: 'High', category: 'Cereal' },
  { name: 'Wheat', emoji: '🌿', score: 88, season: 'Rabi', soilType: 'Loamy', water: 'Medium', category: 'Cereal' },
  { name: 'Maize', emoji: '🌽', score: 85, season: 'Kharif', soilType: 'Well-drained', water: 'Medium', category: 'Cereal' },
  { name: 'Cotton', emoji: '☁️', score: 82, season: 'Kharif', soilType: 'Black', water: 'Medium', category: 'Fiber' },
  { name: 'Sugarcane', emoji: '🎋', score: 80, season: 'Annual', soilType: 'Loamy', water: 'High', category: 'Cash Crop' },
  { name: 'Soybean', emoji: '🫘', score: 78, season: 'Kharif', soilType: 'Clay Loam', water: 'Medium', category: 'Pulse' },
  { name: 'Groundnut', emoji: '🥜', score: 76, season: 'Kharif', soilType: 'Sandy Loam', water: 'Low-Medium', category: 'Oilseed' },
  { name: 'Tomato', emoji: '🍅', score: 74, season: 'Year-round', soilType: 'Well-drained', water: 'Medium', category: 'Vegetable' },
  { name: 'Potato', emoji: '🥔', score: 72, season: 'Rabi', soilType: 'Sandy Loam', water: 'Medium', category: 'Vegetable' },
  { name: 'Chilli', emoji: '🌶️', score: 70, season: 'Year-round', soilType: 'Well-drained', water: 'Low-Medium', category: 'Spice' },
  { name: 'Banana', emoji: '🍌', score: 68, season: 'Year-round', soilType: 'Loamy', water: 'High', category: 'Fruit' },
  { name: 'Mango', emoji: '🥭', score: 65, season: 'Perennial', soilType: 'Well-drained', water: 'Medium', category: 'Fruit' },
]

const categories = ['All', 'Cereal', 'Vegetable', 'Fruit', 'Pulse', 'Oilseed', 'Fiber', 'Cash Crop', 'Spice']

export default function BrowseCrops() {
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [searchQuery, setSearchQuery] = useState('')

  const filteredCrops = crops.filter((crop) => {
    const matchesCategory = selectedCategory === 'All' || crop.category === selectedCategory
    const matchesSearch = crop.name.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.05 } },
  }

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  }

  return (
    <div className="min-h-screen py-8 lg:py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-12"
      >
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight font-display text-neutral-900 dark:text-white mb-4">
          Browse Crops
        </h1>
        <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto">
          Explore our database of crops and their ideal soil conditions.
        </p>
      </motion.div>

      {/* Search */}
      <div className="max-w-md mx-auto mb-8">
        <div className="relative">
          <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search crops..."
            className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-900 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder-neutral-400 focus:border-forest-500 focus:ring-2 focus:ring-forest-500/20 focus:outline-none transition-all"
          />
        </div>
      </div>

      {/* Categories */}
      <div className="flex flex-wrap justify-center gap-2 mb-10">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
              selectedCategory === cat
                ? 'bg-forest-600 text-white shadow-md shadow-forest-600/20'
                : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Crop Grid */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
      >
        {filteredCrops.map((crop) => (
          <motion.div key={crop.name} variants={item}>
            <Card variant="glass" className="p-6 h-full">
              <div className="text-4xl mb-3">{crop.emoji}</div>
              <h3 className="text-xl font-bold text-neutral-900 dark:text-white mb-1">{crop.name}</h3>
              <Badge
                variant={crop.score >= 85 ? 'success' : crop.score >= 70 ? 'secondary' : 'warning'}
                size="sm"
                className="mb-3"
              >
                {crop.score}% match
              </Badge>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Season</span>
                  <span className="font-medium text-neutral-700 dark:text-neutral-300">{crop.season}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Soil</span>
                  <span className="font-medium text-neutral-700 dark:text-neutral-300">{crop.soilType}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Water</span>
                  <span className="font-medium text-neutral-700 dark:text-neutral-300">{crop.water}</span>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {filteredCrops.length === 0 && (
        <div className="text-center py-16">
          <span className="text-6xl mb-4 block">🌾</span>
          <h3 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">No crops found</h3>
          <p className="text-neutral-500 dark:text-neutral-400">Try adjusting your search or filter criteria.</p>
        </div>
      )}
    </div>
  )
}