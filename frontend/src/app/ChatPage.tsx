import { Send, Paperclip, Mic, Image, FileText, Loader2 } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import { clsx } from 'clsx'
import { api } from '@lib/api'
import { Message } from '@components/Message'
import { MessageInput } from '@components/MessageInput'

export function ChatPage() {
  const [messages, setMessages] = useState<Array<{
    id: string
    role: 'user' | 'assistant'
    content: string
    citations?: Array<{ id: string; text: string }>
    loading?: boolean
  }>>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = {
      id: crypto.randomUUID(),
      role: 'user' as const,
      content: input,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await api.post('/v1/chat', {
        query: input,
        stream: false,
      })

      const assistantMessage = {
        id: crypto.randomUUID(),
        role: 'assistant' as const,
        content: response.data.answer,
        citations: response.data.citations,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = {
        id: crypto.randomUUID(),
        role: 'assistant' as const,
        content: 'Sorry, I encountered an error. Please try again.',
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-200px)]">
      <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin" ref={scrollAreaRef}>
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}
        {loading && (
          <div className="flex justify-center py-4">
            <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSend} className="border-t border-gray-200 p-4 bg-white">
        <MessageInput
          value={input}
          onChange={setInput}
          onSubmit={handleSend}
          disabled={loading}
        />
      </form>
    </div>
  )
}