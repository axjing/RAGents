import { Send, Paperclip, Mic, Image, FileText, Smile } from 'lucide-react'
import { clsx } from 'clsx'
import { ForwardedRef, useImperativeHandle, forwardRef } from 'react'

interface MessageInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (e: React.FormEvent) => void
  disabled?: boolean
  ref?: ForwardedRef<HTMLFormElement>
}

export const MessageInput = forwardRef<HTMLFormElement, MessageInputProps>(
  ({ value, onChange, onSubmit, disabled }, ref) => {
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    useImperativeHandle(ref, () => ({
      focus: () => textareaRef.current?.focus(),
      clear: () => onChange(''),
    }))

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        if (value.trim() && !disabled) {
          onSubmit(e as unknown as React.FormEvent)
        }
      }
    }

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange(e.target.value)
    }

    return (
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={value}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              placeholder="Type a message... (Shift+Enter for new line)"
              className={clsx(
                'w-full min-h-[44px] max-h-[200px] px-4 py-3 pr-12 rounded-xl border bg-white resize-none',
                'focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500',
                'disabled:bg-gray-50 disabled:cursor-not-allowed',
                'text-sm leading-relaxed'
              )}
              rows={1}
              style={{ height: 'auto' }}
            />
            <div className="absolute right-3 bottom-3 flex items-center gap-1">
              <button
                type="button"
                className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                aria-label="Attach file"
              >
                <Paperclip className="h-5 w-5" />
              </button>
              <button
                type="button"
                className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                aria-label="Add image"
              >
                <Image className="h-5 w-5" />
              </button>
              <button
                type="button"
                className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                aria-label="Voice input"
              >
                <Mic className="h-5 w-5" />
              </button>
              <button
                type="button"
                className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                aria-label="Emoji"
              >
                <Smile className="h-5 w-5" />
              </button>
            </div>
          </div>
          <button
            type="submit"
            disabled={disabled || !value.trim()}
            className={clsx(
              'flex-shrink-0 p-2.5 rounded-xl transition-colors',
              'bg-primary-600 text-white hover:bg-primary-700',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
            aria-label="Send message"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
        <p className="text-xs text-gray-400 text-center">
          Press <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-600 font-mono">Enter</kbd> to send,{' '}
          <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-600 font-mono">Shift+Enter</kbd> for new line
        </p>
      </form>
    )
  }
)

MessageInput.displayName = 'MessageInput'

import { useRef } from 'react'