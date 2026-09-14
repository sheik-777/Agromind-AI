import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import SeedToMango3D from '@/components/loading/SeedToMango3D'
import { api } from '@/services/api'

const processingStages = [
  '🌱 Uploading report...',
  '📄 Converting PDF...',
  '🔍 Reading report...',
  '🧪 Extracting soil parameters...',
  '📊 Analysing soil...',
  '🌾 Comparing crop database...',
  '🤖 Running recommendation engine...',
  '✨ Preparing dashboard...',
]

export default function AnalyzeSoil() {
  const navigate = useNavigate()
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingStage, setProcessingStage] = useState(0)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file)
      setError(null)
    } else {
      setError('Please upload a PDF file')
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
    }
  }, [])

  const handleAnalyze = async () => {
    if (!selectedFile) return

    setIsProcessing(true)
    setProcessingStage(0)
    setUploadProgress(0)
    setError(null)

    let stageInterval: ReturnType<typeof setInterval> | null = null

    try {
      // Simulate progress stages
      stageInterval = setInterval(() => {
        setProcessingStage((prev) => {
          if (prev >= processingStages.length - 1) {
            if (stageInterval) clearInterval(stageInterval)
            return prev
          }
          return prev + 1
        })
      }, 3000)

      const response = await api.uploadSoilReport(selectedFile)

      if (response.success) {
        sessionStorage.setItem('soilReport', JSON.stringify(response))
        navigate('/results')
      } else {
        setError(response.message || 'Analysis failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during analysis')
    } finally {
      if (stageInterval) clearInterval(stageInterval)
      setIsProcessing(false)
      setProcessingStage(0)
    }
  }

  const handleReset = () => {
    setSelectedFile(null)
    setError(null)
    setUploadProgress(0)
    setProcessingStage(0)
  }

  if (isProcessing) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <Card variant="glass" className="w-full max-w-lg p-8">
          <SeedToMango3D currentStep={processingStage} />
          <div className="mt-8">
            <div className="flex justify-between text-sm text-neutral-600 dark:text-neutral-400 mb-2">
              <span>Processing {selectedFile?.name}</span>
              <span>{Math.round(uploadProgress)}%</span>
            </div>
            <div className="h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-forest-600 to-emerald-500 rounded-full"
                animate={{ width: `${uploadProgress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-[80vh] py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-12"
      >
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight font-display text-neutral-900 dark:text-white mb-4">
          Analyze Your Soil
        </h1>
        <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto">
          Upload your soil lab report and get instant AI-powered analysis and crop recommendations.
        </p>
      </motion.div>

      <div className="max-w-2xl mx-auto">
        <AnimatePresence mode="wait">
          {!selectedFile ? (
            <motion.div
              key="dropzone"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              {/* Drop zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                  'relative border-2 border-dashed rounded-3xl p-12 text-center transition-all duration-300 cursor-pointer group',
                  isDragging
                    ? 'border-forest-500 bg-forest-50 dark:bg-forest-950/20 scale-[1.02]'
                    : 'border-neutral-300 dark:border-neutral-700 hover:border-forest-400 dark:hover:border-forest-600 hover:bg-neutral-50 dark:hover:bg-neutral-900/50'
                )}
                onClick={() => document.getElementById('file-input')?.click()}
              >
                <input
                  id="file-input"
                  type="file"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                <motion.div
                  animate={isDragging ? { scale: 1.1, y: -5 } : { scale: 1, y: 0 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                  className="mb-6"
                >
                  <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-forest-100 to-emerald-100 dark:from-forest-900/30 dark:to-emerald-900/30 flex items-center justify-center group-hover:shadow-lg group-hover:shadow-forest-500/10 transition-shadow duration-300">
                    <svg className="w-10 h-10 text-forest-600 dark:text-forest-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
                    </svg>
                  </div>
                </motion.div>

                <h3 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">
                  {isDragging ? 'Drop your report here' : 'Upload Soil Report'}
                </h3>
                <p className="text-neutral-500 dark:text-neutral-400 mb-4">
                  Drag & drop your PDF file here, or click to browse
                </p>
                <p className="text-sm text-neutral-400 dark:text-neutral-500">
                  Supports PDF format • Max 10MB
                </p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="file-selected"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              {/* File preview */}
              <Card variant="glass" className="p-6 mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-red-100 to-red-50 dark:from-red-900/30 dark:to-red-900/20 flex items-center justify-center flex-shrink-0">
                    <svg className="w-7 h-7 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-neutral-900 dark:text-white truncate">
                      {selectedFile.name}
                    </h4>
                    <p className="text-sm text-neutral-500 dark:text-neutral-400">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    onClick={handleReset}
                    className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                  >
                    <svg className="w-5 h-5 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </Card>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800"
                >
                  <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                </motion.div>
              )}

              {/* Analyze button */}
              <Button
                onClick={handleAnalyze}
                size="lg"
                className="w-full text-lg"
                isLoading={isProcessing}
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
                Analyze Soil Report
              </Button>

              {/* What happens next */}
              <div className="mt-8 grid grid-cols-2 gap-4">
                {[
                  { icon: '🔬', text: 'Extract 18+ soil parameters' },
                  { icon: '📊', text: 'Visualize soil health' },
                  { icon: '🌾', text: 'Match best crops' },
                  { icon: '📋', text: 'Get recommendations' },
                ].map((item) => (
                  <div key={item.text} className="flex items-center gap-3 text-sm text-neutral-600 dark:text-neutral-400">
                    <span className="text-lg">{item.icon}</span>
                    <span>{item.text}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}