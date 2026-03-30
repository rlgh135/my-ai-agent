import { useCallback, useRef } from 'react'
import { useChatStore } from '@/store/chatStore'
import { useSessionStore } from '@/store/sessionStore'
import { useTaskStore } from '@/store/taskStore'

/**
 * useSSE — POST /api/chat SSE 스트리밍 전송
 * 이벤트 타입:
 *   data: { type: 'delta', content: '...' }
 *   data: { type: 'done', content: '...' , token_usage: {...} }
 *   data: { type: 'task_pending', task: { id, description, ... } }
 *   data: { type: 'error', message: '...' }
 */
export function useSSE() {
  const abortRef = useRef(null)
  const { setStreaming, clearStreaming, setTokenUsage } = useChatStore()
  const { appendMessage, updateLastAssistantMessage, finalizeAssistantMessage } = useSessionStore()
  const { addPendingTask } = useTaskStore()

  const sendMessage = useCallback(async (userMessage) => {
    // 스토어에서 직접 최신 activeSessionId를 읽는다.
    // useCallback 클로저로 캡처하면 createSession() 직후 stale 값이 남아
    // 첫 메시지가 전송되지 않는 문제가 생긴다.
    const { activeSessionId } = useSessionStore.getState()
    if (!activeSessionId) return

    // 사용자 메시지 즉시 추가
    appendMessage({
      id: `usr-${Date.now()}`,
      role: 'user',
      content: userMessage,
      createdAt: new Date().toISOString(),
    })

    // 스트리밍 AI 메시지 placeholder 추가
    appendMessage({
      id: `ast-${Date.now()}`,
      role: 'assistant',
      content: '',
      streaming: true,
      createdAt: new Date().toISOString(),
    })

    setStreaming(true)
    const ctrl = new AbortController()
    abortRef.current = ctrl

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify({ session_id: activeSessionId, message: userMessage }),
        signal: ctrl.signal,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Stream request failed')
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // 마지막 불완전 줄 보관

        for (const line of lines) {
          if (!line.startsWith('data:')) continue
          const raw = line.slice(5).trim()
          if (!raw || raw === '[DONE]') continue

          let event
          try { event = JSON.parse(raw) } catch { continue }

          if (event.type === 'delta') {
            updateLastAssistantMessage(event.content)

          } else if (event.type === 'done') {
            finalizeAssistantMessage(event.content)
            if (event.token_usage) setTokenUsage(event.token_usage)

          } else if (event.type === 'task_pending') {
            addPendingTask(event.task)

          } else if (event.type === 'error') {
            const icons = {
              insufficient_credits: '💳',
              auth_failed: '🔑',
              rate_limit: '⏱️',
              permission_denied: '🚫',
              connection_error: '🌐',
              server_error: '🖥️',
            }
            const icon = icons[event.error_code] || '⚠️'
            finalizeAssistantMessage(`${icon} ${event.message}`)
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        finalizeAssistantMessage(`⚠️ 연결 오류: ${err.message}`)
      }
    } finally {
      clearStreaming()
      abortRef.current = null
    }
  // activeSessionId를 dependency에서 제거 — 매 호출 시 getState()로 최신 값을 읽는다
  }, [appendMessage, updateLastAssistantMessage, finalizeAssistantMessage, setStreaming, clearStreaming, setTokenUsage, addPendingTask])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { sendMessage, cancel }
}
