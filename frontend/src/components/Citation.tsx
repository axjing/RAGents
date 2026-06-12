import { FileText, ExternalLink } from 'lucide-react'
import { clsx } from 'clsx'

interface CitationProps {
  citation: {
    id: string
    text: string
    document_title?: string
    page?: number
  }
  index: number
}

export function Citation({ citation, index }: CitationProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium transition-colors',
        'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200'
      )}
      title={citation.text}
    >
      <FileText className="h-3 w-3" />
      <span>[{index}]</span>
      {citation.document_title && (
        <span className="truncate max-w-[150px]">{citation.document_title}</span>
      )}
      {citation.page && (
        <span className="text-gray-400">p.{citation.page}</span>
      )}
    </button>
  )
}