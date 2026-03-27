import { PanelLeftClose, PanelLeftOpen, Settings } from 'lucide-react'
import { useUiStore } from '@/store/uiStore'
import { useSessionStore } from '@/store/sessionStore'
import { useChatStore } from '@/store/chatStore'
import TokenBadge from '@/components/common/TokenBadge'

export default function Header() {
  const { sidebarCollapsed, toggleSidebar, view, openSettings } = useUiStore()
  const { sessions, activeSessionId } = useSessionStore()
  const { tokenUsage } = useChatStore()

  const activeSession = sessions.find(s => s.id === activeSessionId)

  const viewLabel = {
    chat: activeSession?.title || '새 대화',
    files: '파일 탐색기',
    settings: '설정',
  }

  return (
    <header
      className="flex items-center gap-3 px-4 h-14 border-b shrink-0"
      style={{ background: 'var(--color-surface-0)', borderColor: 'var(--color-surface-200)' }}
    >
      {/* 사이드바 토글 */}
      <button
        onClick={toggleSidebar}
        className="p-1.5 rounded-md transition-colors"
        style={{ color: 'var(--color-ink-500)' }}
        title={sidebarCollapsed ? '사이드바 열기' : '사이드바 닫기'}
      >
        {sidebarCollapsed
          ? <PanelLeftOpen size={17} />
          : <PanelLeftClose size={17} />
        }
      </button>

      {/* 현재 뷰 제목 */}
      <h1 className="flex-1 text-sm font-semibold truncate" style={{ color: 'var(--color-ink-900)' }}>
        {viewLabel[view]}
      </h1>

      {/* 토큰 배지 (채팅 뷰에서만) */}
      {view === 'chat' && activeSessionId && (
        <TokenBadge usage={tokenUsage} />
      )}

      {/* 설정 버튼 */}
      <button
        onClick={openSettings}
        className="p-1.5 rounded-md transition-colors"
        style={{ color: 'var(--color-ink-500)' }}
        title="설정"
      >
        <Settings size={17} />
      </button>
    </header>
  )
}
