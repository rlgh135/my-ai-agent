import { useState, useRef, useCallback } from 'react'
import { Send, Square, Paperclip } from 'lucide-react'
import clsx from 'clsx'
import { useChatStore } from '@/store/chatStore'

const QUICK_COMMANDS = [
  { label: '파일 읽기', value: '다음 파일을 읽어줘: ' },
  { label: '파일 생성', value: '다음 내용으로 파일을 만들어줘: ' },
  { label: '웹 검색', value: '다음 내용을 웹에서 검색해줘: ' },
  { label: '이메일 발송', value: '다음 내용으로 이메일을 보내줘: ' },
]

export default function MessageInput({ onSend, onCancel }) {
  const [value, setValue] = useState('')
  const [showHints, setShowHints] = useState(false)
  const textareaRef = useRef(null)
  const { isStreaming } = useChatStore()

  const handleSend = useCallback(() => {
    const msg = value.trim()
    if (!msg || isStreaming) return
    onSend(msg)
    setValue('')
    setShowHints(false)
    // 높이 리셋
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }, [value, isStreaming, onSend])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e) => {
    setValue(e.target.value)
    // 자동 높이 조절
    const el = e.target
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  const applyQuickCommand = (cmd) => {
    setValue(cmd.value)
    setShowHints(false)
    textareaRef.current?.focus()
  }

  return (
    <div
      className="border-t px-4 py-3"
      style={{ background: 'var(--color-surface-0)', borderColor: 'var(--color-surface-200)' }}
    >
      {/* 빠른 명령 힌트 */}
      {showHints && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {QUICK_COMMANDS.map(cmd => (
            <button
              key={cmd.label}
              onClick={() => applyQuickCommand(cmd)}
              className="px-2.5 py-1 rounded-full text-[11px] font-medium transition-colors border"
              style={{
                background: 'var(--color-surface-50)',
                borderColor: 'var(--color-surface-300)',
                color: 'var(--color-ink-700)',
              }}
            >
              {cmd.label}
            </button>
          ))}
        </div>
      )}

      {/* 입력창 */}
      <div
        className="flex items-end gap-2 rounded-xl border px-3 py-2 transition-colors"
        style={{
          background: 'var(--color-surface-100)',
          borderColor: 'var(--color-surface-300)',
        }}
      >
        {/* 빠른 명령 토글 */}
        <button
          onClick={() => setShowHints(v => !v)}
          className="p-1 rounded-md shrink-0 mb-0.5 transition-colors"
          style={{ color: showHints ? 'var(--color-brand-600)' : 'var(--color-ink-300)' }}
          title="빠른 명령"
        >
          <Paperclip size={16} />
        </button>

        {/* 텍스트 영역 */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="메시지를 입력하세요… (Shift+Enter: 줄바꿈)"
          rows={1}
          className="flex-1 resize-none bg-transparent text-sm outline-none leading-relaxed"
          style={{
            color: 'var(--color-ink-900)',
            minHeight: '24px',
            maxHeight: '160px',
          }}
        />

        {/* 전송 / 중지 버튼 */}
        {isStreaming ? (
          <button
            onClick={onCancel}
            className="p-1.5 rounded-lg shrink-0 mb-0.5 transition-colors"
            style={{ background: 'var(--color-danger-500)', color: '#fff' }}
            title="생성 중지"
          >
            <Square size={14} />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!value.trim()}
            className={clsx(
              'p-1.5 rounded-lg shrink-0 mb-0.5 transition-colors',
              value.trim()
                ? 'text-white'
                : 'cursor-not-allowed'
            )}
            style={{
              background: value.trim() ? 'var(--color-brand-600)' : 'var(--color-surface-200)',
              color: value.trim() ? '#fff' : 'var(--color-ink-300)',
            }}
            title="전송 (Enter)"
          >
            <Send size={14} />
          </button>
        )}
      </div>

      <p className="mt-1.5 text-[10px] text-center" style={{ color: 'var(--color-ink-300)' }}>
        AI는 실수할 수 있습니다. 중요한 파일은 반드시 백업하세요.
      </p>
    </div>
  )
}
