import { useState, useRef, useEffect, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { api, type AiAskResponse } from '@/services/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  meta?: {
    intent?: string
    sources?: { title: string; source: string }[]
    fieldUsed?: boolean
    warning?: string
    answerMode?: string
  }
}

const SUGGESTED_QUESTIONS = [
  'What crop suits sandy soil?',
  'Why are my leaves turning yellow?',
  'When should I irrigate?',
  'How can I improve soil fertility?',
  'What should I plant this season?',
  'Explain crop rotation',
  'What is NPK?',
  'How do I control aphids?',
  'My soil pH is 5.2 — what can tolerate it?',
  'What causes nitrogen deficiency?',
  'What fertilizer for rice at vegetative stage?',
  'How much rainfall does wheat need?',
]

export default function AskAgroMind() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm AgroMind AI — grounded in your field data, a 1200-crop dataset, and curated agricultural knowledge.\n\nAsk me anything about soil, crops, irrigation, fertilizer, disease, weather, or organic farming. For the best answers, connect your field sensors or upload a soil report.",
      timestamp: new Date(),
      meta: { answerMode: 'welcome' },
    },
  ])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const askMutation = useMutation<AiAskResponse, Error, { question: string; conversation: { role: string; content: string }[] }>({
    mutationFn: (payload) => api.askAgroMind({ question: payload.question, conversation: payload.conversation }),
    onSuccess: (data, _variables) => {
      const assistantMessage: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: data.answer || data.warning || "I couldn't generate an answer. The server may be unavailable.",
        timestamp: new Date(),
        meta: {
          intent: data.intent,
          sources: data.sources,
          fieldUsed: data.field_context_used,
          warning: data.warning,
          answerMode: data.answer_mode,
        },
      }
      setMessages((prev) => [...prev, assistantMessage])
    },
    onError: (_err, _variables) => {
      const errorMessage: Message = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: 'Could not reach AgroMind AI. Please check the server and try again.',
        timestamp: new Date(),
        meta: { answerMode: 'error' },
      }
      setMessages((prev) => [...prev, errorMessage])
    },
    onSettled: () => {
      // no-op; mutation handles its own state
    },
  })

  const handleSend = (override?: string) => {
    const question = (override || input).trim()
    if (!question || askMutation.isPending) return

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')

    const conversation = messages.slice(-10).map((m) => ({ role: m.role, content: m.content }))
    askMutation.mutate({ question, conversation })
  }

  const clearConversation = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: "Conversation cleared. Ask me a new agricultural question.",
        timestamp: new Date(),
        meta: { answerMode: 'welcome' },
      },
    ])
  }

  return (
    <div className="min-h-[85vh] flex flex-col py-8 lg:py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-6"
      >
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight font-display text-neutral-900 dark:text-white mb-3">
          Ask AgroMind
        </h1>
        <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto">
          Agricultural intelligence grounded in field data, a 1200-crop dataset, and curated knowledge.
        </p>
      </motion.div>

      <div className="flex-1 max-w-3xl mx-auto w-full">
        <Card variant="glass" className="flex flex-col h-[65vh]">
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
                  <div className={`max-w-[85%] ${msg.role === 'user' ? '' : 'space-y-2'}`}>
                    <div
                      className={`px-4 py-3 rounded-2xl ${
                        msg.role === 'user'
                          ? 'bg-forest-600 text-white rounded-br-md'
                          : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-white rounded-bl-md'
                      }`}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    </div>

                    {/* Assistant meta badges */}
                    {msg.role === 'assistant' && msg.meta && (
                      <div className="flex flex-wrap gap-2 pl-1">
                        {msg.meta.intent && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium bg-neutral-200/70 dark:bg-neutral-700/60 text-neutral-600 dark:text-neutral-400">
                            intent: {msg.meta.intent}
                          </span>
                        )}
                        {msg.meta.fieldUsed && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                            field data used
                          </span>
                        )}
                        {msg.meta.answerMode && msg.meta.answerMode !== 'welcome' && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium bg-neutral-200/70 dark:bg-neutral-700/60 text-neutral-600 dark:text-neutral-400">
                            {msg.meta.answerMode}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Sources */}
                    {msg.role === 'assistant' && msg.meta?.sources && msg.meta.sources.length > 1 && (
                      <div className="pl-1">
                        <p className="text-[10px] font-medium text-neutral-500 dark:text-neutral-500 mb-0.5">Sources:</p>
                        <div className="flex flex-wrap gap-1">
                          {msg.meta.sources.filter(s => s.title).map((s, i) => (
                            <span key={i} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] bg-neutral-200/50 dark:bg-neutral-800/50 text-neutral-500 dark:text-neutral-500">
                              {s.source && s.source !== 'AgroMind' ? `[${s.source}] ` : ''}{s.title}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Warning */}
                    {msg.role === 'assistant' && msg.meta?.warning && (
                      <div className="pl-1">
                        <p className="text-[10px] text-amber-600 dark:text-amber-400 italic">{msg.meta.warning}</p>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Typing indicator */}
            {askMutation.isPending && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
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

          {/* Suggested questions (show when few messages) */}
          {messages.length <= 2 && (
            <div className="px-6 pb-3">
              <p className="text-[10px] font-medium text-neutral-500 dark:text-neutral-500 mb-2 uppercase tracking-wide">Try asking:</p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_QUESTIONS.slice(0, 6).map((q) => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); handleSend(q) }}
                    disabled={askMutation.isPending}
                    className="px-3 py-1.5 text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 rounded-full hover:bg-forest-50 dark:hover:bg-forest-950/30 hover:text-forest-600 dark:hover:text-forest-400 transition-colors disabled:opacity-50"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Toolbar */}
          <div className="px-6 py-2 border-t border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
              {messages.length > 2 && (
                <button
                  onClick={clearConversation}
                  className="px-3 py-1.5 text-xs font-medium text-neutral-500 dark:text-neutral-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-lg transition-colors"
                >
                  Clear conversation
                </button>
              )}
            </div>
            <span className="text-[10px] text-neutral-400 dark:text-neutral-600">
              {messages.length - 1} messages
            </span>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-neutral-200 dark:border-neutral-700">
            <form
              onSubmit={(e) => { e.preventDefault(); handleSend() }}
              className="flex gap-3"
            >
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about soil, crops, irrigation, disease…"
                className="flex-1 px-4 py-3 bg-neutral-50 dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder-neutral-400 focus:border-forest-500 focus:ring-2 focus:ring-forest-500/20 focus:outline-none transition-all text-sm"
                disabled={askMutation.isPending}
              />
              <Button type="submit" disabled={!input.trim() || askMutation.isPending} className="px-4">
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