import { useEffect } from 'react'
import { X } from 'lucide-react'

export default function Modal({ open, onClose, title, children, maxWidth = 'max-w-lg' }) {
  // ESC 닫기
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.4)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        className={`relative w-full ${maxWidth} rounded-xl shadow-xl animate-fade-up`}
        style={{ background: 'var(--color-surface-0)' }}
      >
        {/* 헤더 */}
        <div
          className="flex items-center justify-between px-5 py-4 border-b"
          style={{ borderColor: 'var(--color-surface-200)' }}
        >
          <h2 className="text-sm font-semibold" style={{ color: 'var(--color-ink-900)' }}>
            {title}
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-md transition-colors"
            style={{ color: 'var(--color-ink-500)' }}
          >
            <X size={16} />
          </button>
        </div>

        {/* 본문 */}
        <div className="px-5 py-4">
          {children}
        </div>
      </div>
    </div>
  )
}
