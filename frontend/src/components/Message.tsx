import { Bot, User, Loader2, Quote } from 'lucide-react'
import { clsx } from 'clsx'
import ReactMarkdown from 'react-markdown'
import { Citation } from './Citation'

interface MessageProps {
  message: {
    id: string
    role: 'user' | 'assistant'
    content: string
    citations?: Array<{ id: string; text: string }>
    loading?: boolean
  }
}

export function Message({ message }: MessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={clsx('flex gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={clsx(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
          isUser ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600'
        )}
        aria-hidden="true"
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div
        className={clsx(
          'max-w-[70%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-primary-600 text-white rounded-br-md'
            : 'bg-white text-gray-900 rounded-bl-md shadow-sm border border-gray-100'
        )}
      >
        {message.loading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Thinking...</span>
          </div>
        ) : (
          <ReactMarkdown
            className={clsx('prose prose-sm max-w-none', isUser ? 'prose-invert' : '')}
            components={{
              a: ({ href, children }) => (
                <a href={href} className="underline hover:text-primary-600" target="_blank" rel="noopener">
                  {children}
                </a>
              ),
              code: ({ children }) => (
                <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono">
                  {children}
                </code>
              ),
              pre: ({ children }) => (
                <pre className="bg-gray-900 p-3 rounded-lg overflow-x-auto text-sm">
                  {children}
                </pre>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="flex flex-wrap gap-2">
              {message.citations.map((citation, index) => (
                <Citation key={citation.id} citation={citation} index={index + 1} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}