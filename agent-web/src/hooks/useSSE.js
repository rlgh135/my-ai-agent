import { useCallback, useRef } from 'react'
import { useChatStore } from '@/store/chatStore'
import { useSessionStore } from '@/store/sessionStore'
import { useTaskStore } from '@/store/taskStore'

/**
 * 백엔드가 snake_case로 전송하는 토큰 usage 데이터를
 * TokenBadge / chatStore가 기대하는 camelCase로 변환한다.
 */
function normalizeTokenUsage(raw) {
  return {
    usedTokens:   raw.used_tokens   ?? raw.usedTokens   ?? 0,
    maxTokens:    raw.max_tokens    ?? raw.maxTokens     ?? 200_000,
    usagePercent: raw.usage_percent ?? raw.usagePercent  ?? 0,
    status:       raw.status ?? 'normal',
  }
}

/**
 * useSSE — POST /api/chat SSE 스트리밍 전송
 * 이벤트 타입:
 *   data: { type: 'delta',       content: '...' }
 *   data: { type: 'done',        content: '...', token_usage: {...} }
 *   data: { type: 'token_usage', used_tokens, max_tokens, usage_percent, status }
 *   data: { type: 'task_pending', task: { id, type, description, payload, createdAt } }
 *   data: { type: 'error',       message: '...', error_code: '...' }
 */
export function useSSE() {
  const abortRef = useRef(null)
  const { setStreaming, clearStreaming, setTokenUsage } = useChatStore()
  const { appendMessage, updateLastAssistantMessage, finalizeAssistantMessage } = useSessionStore()
  const { addPendingTask } = useTaskStore()

  const sendMessage = useCallback(async (userMessage) => {
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
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data:')) continue
          const raw = line.slice(5).trim()
          if (!raw || raw === '[DONE]') continue

          let event
          try { event = JSON.parse(raw) } catch { continue }

          if (event.type === 'delta') {
            updateLastAssistantMessage(event.content)

          } else if (event.type === 'token_usage') {
            // 스트리밍 시작 시 초기 토큰 사용량 (히스토리 기반 근사값)
            setTokenUsage(normalizeTokenUsage(event))

          } else if (event.type === 'done') {
            finalizeAssistantMessage(event.content)
            if (event.token_usage) {
              // 실제 API 응답 기반 정확한 사용량
              setTokenUsage(normalizeTokenUsage(event.token_usage))
            }

          } else if (event.type === 'task_pending') {
            addPendingTask(event.task)

          } else if (event.type === 'error') {
            const icons = {
              insufficient_credits: '💳',
              auth_failed:          '🔑',
              rate_limit:           '⏱️',
              permission_denied:    '🚫',
              connection_error:     '🌐',
              server_error:         '🖥️',
              max_tool_turns:       '🔄',
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
  }, [appendMessage, updateLastAssistantMessage, finalizeAssistantMessage, setStreaming, clearStreaming, setTokenUsage, addPendingTask])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { sendMessage, cancel }
}
