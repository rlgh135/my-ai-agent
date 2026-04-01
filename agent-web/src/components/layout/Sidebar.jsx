import { useEffect, useState } from 'react'
import { MessageSquare, FolderOpen, Settings, Plus, Trash2, Bot, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'
import { useSessionStore } from '@/store/sessionStore'
import { useUiStore } from '@/store/uiStore'
import { relativeTime } from '@/utils/formatters'
import Modal from '@/components/common/Modal'

export default function Sidebar() {
  const { sessions, activeSessionId, isLoadingSessions, fetchSessions, createSession, selectSession, deleteSession } = useSessionStore()
  const { view, setView, sidebarCollapsed } = useUiStore()
  const [confirmTarget, setConfirmTarget] = useState(null) // 삭제 확인 대상 session

  useEffect(() => { fetchSessions() }, [fetchSessions])

  const handleNewChat = async () => {
    await createSession()
    setView('chat')
  }

  const handleDeleteConfirm = async () => {
    if (!confirmTarget) return
    await deleteSession(confirmTarget.id)
    setConfirmTarget(null)
  }

  return (
    <>
    <aside
      className={clsx(
        'flex flex-col h-full shrink-0 transition-all duration-200',
        sidebarCollapsed ? 'w-0 overflow-hidden' : 'w-64',
      )}
      style={{ background: 'var(--color-navy-950)' }}
    >
      {/* 로고 헤더 */}
      <div className="flex items-center gap-2.5 px-4 py-4 border-b" style={{ borderColor: 'var(--color-navy-700)' }}>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'var(--color-brand-600)' }}>
          <Bot size={15} className="text-white" />
        </div>
        <span className="text-sm font-semibold text-white">AI 비서</span>
      </div>

      {/* 새 대화 버튼 */}
      <div className="px-3 pt-3 pb-2">
        <button
          onClick={handleNewChat}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs font-medium transition-colors"
          style={{ color: 'var(--color-navy-600)', background: 'var(--color-navy-800)' }}
          onMouseEnter={e => { e.currentTarget.style.background = 'var(--color-brand-600)'; e.currentTarget.style.color = '#fff' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'var(--color-navy-800)'; e.currentTarget.style.color = 'var(--color-navy-600)' }}
        >
          <Plus size={13} />
          새 대화
        </button>
      </div>

      {/* 세션 목록 */}
      <nav className="flex-1 overflow-y-auto px-2 py-1">
        <p className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--color-navy-600)' }}>
          대화 기록
        </p>

        {isLoadingSessions ? (
          <div className="flex flex-col gap-1.5 px-2 pt-1">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-10 rounded-md animate-pulse" style={{ background: 'var(--color-navy-800)' }} />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <p className="px-2 py-4 text-xs text-center" style={{ color: 'var(--color-navy-600)' }}>
            아직 대화가 없습니다
          </p>
        ) : (
          sessions.map(session => (
            <SessionItem
              key={session.id}
              session={session}
              active={session.id === activeSessionId}
              onSelect={() => { selectSession(session.id); setView('chat') }}
              onDelete={() => setConfirmTarget(session)}
            />
          ))
        )}
      </nav>

      {/* 하단 네비게이션 */}
      <div className="border-t px-2 py-2" style={{ borderColor: 'var(--color-navy-700)' }}>
        <NavBtn icon={<MessageSquare size={15} />} label="채팅" active={view === 'chat'} onClick={() => setView('chat')} />
        <NavBtn icon={<FolderOpen size={15} />} label="파일 탐색기" active={view === 'files'} onClick={() => setView('files')} />
        <NavBtn icon={<Settings size={15} />} label="설정" active={view === 'settings'} onClick={() => setView('settings')} />
      </div>
    </aside>

    {/* 삭제 확인 모달 */}
    <Modal
      open={!!confirmTarget}
      onClose={() => setConfirmTarget(null)}
      title="대화 삭제"
      maxWidth="max-w-sm"
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-start gap-3">
          <AlertTriangle size={18} className="shrink-0 mt-0.5" style={{ color: '#f59e0b' }} />
          <div>
            <p className="text-sm" style={{ color: 'var(--color-ink-700)' }}>
              <strong className="font-medium" style={{ color: 'var(--color-ink-900)' }}>
                "{confirmTarget?.title || '새 대화'}"
              </strong>{' '}
              대화를 삭제하시겠습니까?
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--color-ink-400)' }}>
              삭제된 대화는 복구할 수 없습니다.
            </p>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <button
            onClick={() => setConfirmTarget(null)}
            className="px-4 py-1.5 rounded-lg text-sm border transition-colors"
            style={{
              borderColor: 'var(--color-surface-300)',
              color: 'var(--color-ink-600)',
              background: 'var(--color-surface-100)',
            }}
          >
            취소
          </button>
          <button
            onClick={handleDeleteConfirm}
            className="px-4 py-1.5 rounded-lg text-sm font-medium text-white transition-colors"
            style={{ background: '#dc2626' }}
          >
            삭제
          </button>
        </div>
      </div>
    </Modal>
    </>
  )
}

function SessionItem({ session, active, onSelect, onDelete }) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={e => e.key === 'Enter' && onSelect()}
      className="group flex items-center gap-2 px-2 py-2.5 rounded-md cursor-pointer transition-colors mb-0.5"
      style={{
        background: active ? 'var(--color-navy-800)' : 'transparent',
        color: active ? '#fff' : 'var(--color-navy-600)',
      }}
    >
      <MessageSquare size={13} className="shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium truncate">{session.title || '새 대화'}</p>
        <p className="text-[10px] truncate mt-0.5" style={{ color: 'var(--color-navy-600)' }}>
          {relativeTime(session.updated_at || session.created_at)}
        </p>
      </div>
      <button
        onClick={e => { e.stopPropagation(); onDelete() }}
        className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:text-red-400"
        title="삭제"
      >
        <Trash2 size={11} />
      </button>
    </div>
  )
}

function NavBtn({ icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      title={label}
      className="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-md text-xs transition-colors"
      style={{
        color: active ? '#fff' : 'var(--color-navy-600)',
        background: active ? 'var(--color-brand-600)' : 'transparent',
      }}
    >
      {icon}
      {label}
    </button>
  )
}
