import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const sampleResponses: Record<string, string> = {
  'ph': 'Soil pH measures the acidity or alkalinity of your soil. Most crops prefer a pH between 6.0 and 7.0. If your soil pH is too low (acidic), you can add lime to raise it. If it\'s too high (alkaline), adding sulfur can help lower it.',
  'nitrogen': 'Nitrogen is essential for vegetative plant growth. It\'s a key component of chlorophyll and proteins. If your nitrogen levels are low, consider using nitrogen-rich fertilizers or organic matter like compost.',
  'phosphorus': 'Phosphorus supports root development and flowering. It\'s particularly important during the early growth stages. Bone meal and rock phosphate are good organic sources of phosphorus.',
  'potassium': 'Potassium improves disease resistance and water regulation in plants. It\'s crucial for overall plant health. Sources include wood ash, kelp meal, and potassium sulfate fertilizers.',
  'crop': 'Based on your soil analysis, I can recommend the best crops for your specific conditions. Upload your soil report to get personalized recommendations!',
  'fertilizer': 'The right fertilizer depends on your soil\'s current nutrient levels. A balanced approach is best - avoid over-fertilizing which can harm plants and the environment. Consider getting a soil test first.',
  'water': 'Proper irrigation is crucial for crop health. Different crops have different water needs. Over-watering can lead to root rot, while under-watering stresses plants. Drip irrigation is often the most efficient method.',
  'organic': 'Organic farming focuses on natural methods to maintain soil health. This includes crop rotation, composting, cover cropping, and avoiding synthetic chemicals. It builds healthy soil over time.',
}

function getResponse(input: string): string {
  const lower = input.toLowerCase()

  for (const [keyword, response] of Object.entries(sampleResponses)) {
    if (lower.includes(keyword)) {
      return response
    }
  }

  return `That's a great question! While I'm a demo version, in the full AgroMind AI assistant, I would provide detailed, personalized answers about:\n\n• Soil health and management\n• Crop selection and rotation\n• Fertilizer recommendations\n• Pest and disease management\n• Water management\n• Organic farming practices\n\nFor now, try uploading your soil report for instant AI-powered analysis and crop recommendations!`
}

export default function AskAgroMind() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m AgroMind AI, your smart agriculture assistant. Ask me anything about soil health, crop recommendations, fertilizers, or farming best practices. 🌱',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    // Simulate AI response delay
    setTimeout(() => {
      const response = getResponse(input.trim())
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
      setIsTyping(false)
    }, 1000 + Math.random() * 1000)
  }

  const quickQuestions = [
    'What is soil pH?',
    'How to improve nitrogen?',
    'Best crops for clay soil?',
    'Organic fertilizer tips',
  ]

  return (
    <div className="min-h-[80vh] flex flex-col py-8 lg:py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight font-display text-neutral-900 dark:text-white mb-4">
          AI Assistant
        </h1>
        <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto">
          Ask anything about soil, crops, and farming.
        </p>
      </motion.div>

      {/* Chat area */}
      <div className="flex-1 max-w-3xl mx-auto w-full">
        <Card variant="glass" className="flex flex-col h-[60vh]">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] px-4 py-3 rounded-2xl ${
                      msg.role === 'user'
                        ? 'bg-forest-600 text-white rounded-br-md'
                        : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-white rounded-bl-md'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {isTyping && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="bg-neutral-100 dark:bg-neutral-800 px-4 py-3 rounded-2xl rounded-bl-md">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick questions */}
          {messages.length <= 1 && (
            <div className="px-6 pb-4">
              <div className="flex flex-wrap gap-2">
                {quickQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => setInput(q)}
                    className="px-3 py-1.5 text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 rounded-full hover:bg-forest-50 dark:hover:bg-forest-950/30 hover:text-forest-600 dark:hover:text-forest-400 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-4 border-t border-neutral-200 dark:border-neutral-700">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSend()
              }}
              className="flex gap-3"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about soil, crops, farming..."
                className="flex-1 px-4 py-3 bg-neutral-50 dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder-neutral-400 focus:border-forest-500 focus:ring-2 focus:ring-forest-500/20 focus:outline-none transition-all text-sm"
                disabled={isTyping}
              />
              <Button type="submit" disabled={!input.trim() || isTyping} className="px-4">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </Button>
            </form>
          </div>
        </Card>
      </div>
    </div>
  )
}