import { useEffect, useRef } from 'react'
import { MessageSquare, Plus } from 'lucide-react'
import { useSessionStore } from '@/store/sessionStore'
import { useChatStore } from '@/store/chatStore'
import { useSSE } from '@/hooks/useSSE'
import MessageBubble from './MessageBubble'
import MessageInput from './MessageInput'
import TaskCard from '@/components/tasks/TaskCard'
import { useTaskStore } from '@/store/taskStore'
import SmtpStatusBanner from '@/components/common/SmtpStatusBanner'

export default function ChatWindow() {
  const { messages, isLoadingMessages, activeSessionId, createSession } = useSessionStore()
  const { isStreaming } = useChatStore()
  const { pendingTasks } = useTaskStore()
  const { sendMessage, cancel } = useSSE()
  const bottomRef = useRef(null)

  // 새 메시지마다 스크롤
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, isStreaming])

  const handleSend = async (msg) => {
    // 세션이 없으면 자동 생성
    if (!activeSessionId) {
      await createSession()
    }
    sendMessage(msg)
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* SMTP 미설정/연결 실패 시 경고 배너 */}
      <SmtpStatusBanner />

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto" style={{ background: 'var(--color-surface-50)' }}>
        {isLoadingMessages ? (
          <LoadingSkeleton />
        ) : messages.length === 0 ? (
          <EmptyState onNewChat={handleSend} />
        ) : (
          <div className="flex flex-col gap-5 px-4 pt-4 pb-6">
            {messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* 대기 중인 작업 협의 카드 */}
            {pendingTasks.length > 0 && (
              <div className="flex flex-col gap-3">
                {pendingTasks.map(task => (
                  <TaskCard key={task.id} task={task} />
                ))}
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* 입력창 */}
      <MessageInput onSend={handleSend} onCancel={cancel} />
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-6">
      {[...Array(3)].map((_, i) => (
        <div key={i} className={`flex gap-3 ${i % 2 === 1 ? 'flex-row-reverse' : ''}`}>
          <div className="w-8 h-8 rounded-full animate-pulse" style={{ background: 'var(--color-surface-200)' }} />
          <div className="flex flex-col gap-1.5" style={{ width: '60%' }}>
            <div className="h-10 rounded-2xl animate-pulse" style={{ background: 'var(--color-surface-200)' }} />
            <div className="h-3 w-16 rounded animate-pulse" style={{ background: 'var(--color-surface-200)' }} />
          </div>
        </div>
      ))}
    </div>
  )
}

function EmptyState({ onNewChat }) {
  const suggestions = [
    '현재 디렉토리의 파일 목록을 보여줘',
    'React 컴포넌트 작성 방법을 설명해줘',
    '프로젝트 구조를 분석해줘',
    '최신 Python 트렌드를 검색해줘',
  ]

  return (
    <div className="flex flex-col items-center justify-center h-full gap-8 px-6">
      <div className="text-center">
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-4"
          style={{ background: 'var(--color-brand-100)' }}>
          <MessageSquare size={22} style={{ color: 'var(--color-brand-600)' }} />
        </div>
        <h2 className="text-lg font-semibold mb-1.5" style={{ color: 'var(--color-ink-900)' }}>
          무엇을 도와드릴까요?
        </h2>
        <p className="text-sm" style={{ color: 'var(--color-ink-400)' }}>
          파일 작업, 웹 검색, 이메일 발송 등을 도와드립니다
        </p>
      </div>

      {/* 제안 카드 */}
      <div className="grid grid-cols-2 gap-2 w-full">
        {suggestions.map(s => (
          <button
            key={s}
            onClick={() => onNewChat(s)}
            className="text-left px-4 py-3 rounded-xl border text-sm transition-all hover:shadow-sm"
            style={{
              background: 'var(--color-surface-0)',
              borderColor: 'var(--color-surface-200)',
              color: 'var(--color-ink-600)',
            }}
          >
            <Plus size={11} className="mb-1.5" style={{ color: 'var(--color-brand-400)' }} />
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
