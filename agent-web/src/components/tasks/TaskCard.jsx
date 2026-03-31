import { useState } from 'react'
import { CheckCircle2, XCircle, Clock, AlertTriangle } from 'lucide-react'
import ToolBadge from '@/components/common/ToolBadge'
import { useTaskStore } from '@/store/taskStore'

const TASK_TYPE_LABELS = {
  filesystem_create: '파일 생성',
  filesystem_update: '파일 수정',
  filesystem_backup: '파일 백업',
  filesystem_delete: '파일 삭제',
  email_send:        '이메일 발송',
}

export default function TaskCard({ task }) {
  const { approveTask, rejectTask } = useTaskStore()
  const [loading, setLoading] = useState(false)

  const handleApprove = async () => {
    setLoading(true)
    try { await approveTask(task.id) } finally { setLoading(false) }
  }
  const handleReject = async () => {
    setLoading(true)
    try { await rejectTask(task.id) } finally { setLoading(false) }
  }

  return (
    <div
      className="rounded-xl border-l-4 overflow-hidden animate-slide-in"
      style={{
        borderLeftColor: 'var(--color-brand-600)',
        background: 'var(--color-surface-0)',
        border: '1px solid var(--color-surface-200)',
        borderLeft: '4px solid var(--color-brand-600)',
      }}
    >
      {/* 헤더 */}
      <div
        className="flex items-center justify-between px-4 py-2.5"
        style={{ background: 'var(--color-brand-50)' }}
      >
        <div className="flex items-center gap-2">
          <AlertTriangle size={14} style={{ color: 'var(--color-brand-600)' }} />
          <span className="text-xs font-semibold" style={{ color: 'var(--color-brand-700)' }}>
            작업 승인 요청
          </span>
        </div>
        <ToolBadge tool={task.type} />
      </div>

      {/* 본문 */}
      <div className="px-4 py-3">
        <p className="text-sm font-medium mb-2" style={{ color: 'var(--color-ink-900)' }}>
          {TASK_TYPE_LABELS[task.type] ?? task.type}
        </p>
        <p className="text-xs mb-3" style={{ color: 'var(--color-ink-500)' }}>
          {task.description}
        </p>

        {/* 페이로드 미리보기 */}
        {task.payload?.path && (
          <div
            className="rounded-md px-3 py-1.5 mb-3 font-mono text-xs"
            style={{ background: 'var(--color-surface-100)', color: 'var(--color-ink-700)' }}
          >
            {task.payload.path}
          </div>
        )}

        {/* 내용 미리보기 (파일 create/update) */}
        {task.payload?.content && (
          <div
            className="rounded-md px-3 py-2 mb-3 font-mono text-[11px] max-h-32 overflow-y-auto whitespace-pre-wrap"
            style={{ background: '#1e1e2e', color: '#e2e8f0' }}
          >
            {task.payload.content.slice(0, 400)}
            {task.payload.content.length > 400 && '\n… (생략됨)'}
          </div>
        )}

        {/* 5분 타임아웃 경고 */}
        <div className="flex items-center gap-1 mb-3">
          <Clock size={11} style={{ color: 'var(--color-ink-300)' }} />
          <span className="text-[10px]" style={{ color: 'var(--color-ink-300)' }}>
            5분 내에 응답하지 않으면 자동 거부됩니다
          </span>
        </div>

        {/* 버튼 */}
        <div className="flex gap-2">
          <button
            onClick={handleApprove}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium transition-colors text-white"
            style={{ background: 'var(--color-success-500)' }}
          >
            <CheckCircle2 size={13} />
            승인
          </button>
          <button
            onClick={handleReject}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium transition-colors"
            style={{
              background: 'var(--color-surface-100)',
              border: '1px solid var(--color-surface-300)',
              color: 'var(--color-ink-700)',
            }}
          >
            <XCircle size={13} style={{ color: 'var(--color-danger-500)' }} />
            거부
          </button>
        </div>
      </div>
    </div>
  )
}

