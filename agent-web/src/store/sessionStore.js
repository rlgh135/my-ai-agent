import { create } from 'zustand'
import * as sessionApi from '@/api/sessions'
import * as chatApi from '@/api/chat'
import { useChatStore } from '@/store/chatStore'

/** 백엔드 snake_case → camelCase 변환 (chatStore / TokenBadge 기대 형식) */
function normalizeTokenUsage(raw) {
  return {
    usedTokens:   raw.used_tokens   ?? raw.usedTokens   ?? 0,
    maxTokens:    raw.max_tokens    ?? raw.maxTokens     ?? 200_000,
    usagePercent: raw.usage_percent ?? raw.usagePercent  ?? 0,
    status:       raw.status ?? 'normal',
  }
}

const EMPTY_TOKEN_USAGE = {
  status: 'normal',
  usagePercent: 0,
  usedTokens: 0,
  maxTokens: 200_000,
}

export const useSessionStore = create((set, get) => ({
  sessions: [],
  activeSessionId: null,
  messages: [],
  isLoadingSessions: false,
  isLoadingMessages: false,

  fetchSessions: async () => {
    set({ isLoadingSessions: true })
    try {
      const data = await sessionApi.listSessions()
      const sessions = Array.isArray(data) ? data : (data.sessions ?? [])
      set({ sessions })
      // 새로고침 후 activeSessionId가 없으면 가장 최근 세션 자동 복원
      if (!get().activeSessionId && sessions.length > 0) {
        await get().selectSession(sessions[0].id)
      }
    } finally {
      set({ isLoadingSessions: false })
    }
  },

  createSession: async (title = '새 대화') => {
    const session = await sessionApi.createSession({ title })
    // 새 세션: 토큰 사용량 초기화
    useChatStore.getState().setTokenUsage(EMPTY_TOKEN_USAGE)
    set(s => ({ sessions: [session, ...s.sessions], activeSessionId: session.id, messages: [] }))
    return session
  },

  selectSession: async (sessionId) => {
    if (get().activeSessionId === sessionId) return

    // 전환 즉시 토큰 배지 초기화 (이전 세션 잔상 제거)
    useChatStore.getState().setTokenUsage(EMPTY_TOKEN_USAGE)
    set({ activeSessionId: sessionId, messages: [], isLoadingMessages: true })

    try {
      // 메시지 로드 + 토큰 사용량 병렬 조회
      const [msgData, tokenData] = await Promise.allSettled([
        sessionApi.getMessages(sessionId),
        chatApi.getTokenUsage(sessionId),
      ])

      if (msgData.status === 'fulfilled') {
        const raw = msgData.value
        const list = Array.isArray(raw) ? raw : (raw.messages ?? [])
        // 백엔드 snake_case → 프론트엔드 camelCase 정규화
        set({ messages: list.map(m => ({ ...m, createdAt: m.createdAt ?? m.created_at })) })
      }

      if (tokenData.status === 'fulfilled' && tokenData.value) {
        useChatStore.getState().setTokenUsage(normalizeTokenUsage(tokenData.value))
      }
    } finally {
      set({ isLoadingMessages: false })
    }
  },

  deleteSession: async (sessionId) => {
    await sessionApi.deleteSession(sessionId)
    set(s => {
      const sessions = s.sessions.filter(x => x.id !== sessionId)
      const activeSessionId = s.activeSessionId === sessionId
        ? (sessions[0]?.id ?? null)
        : s.activeSessionId
      // 삭제 후 활성 세션 없으면 토큰 배지 초기화
      if (activeSessionId === null) {
        useChatStore.getState().setTokenUsage(EMPTY_TOKEN_USAGE)
      }
      return { sessions, activeSessionId, messages: activeSessionId === null ? [] : s.messages }
    })
  },

  appendMessage: (msg) => {
    set(s => ({ messages: [...s.messages, msg] }))
  },

  updateLastAssistantMessage: (delta) => {
    set(s => {
      const msgs = [...s.messages]
      const lastIdx = msgs.findLastIndex(m => m.role === 'assistant')
      if (lastIdx === -1) return {}
      msgs[lastIdx] = { ...msgs[lastIdx], content: msgs[lastIdx].content + delta }
      return { messages: msgs }
    })
  },

  finalizeAssistantMessage: (content) => {
    set(s => {
      const msgs = [...s.messages]
      const lastIdx = msgs.findLastIndex(m => m.role === 'assistant')
      if (lastIdx === -1) return {}
      msgs[lastIdx] = { ...msgs[lastIdx], content, streaming: false, thinking: false }
      return { messages: msgs }
    })
  },

  setLastAssistantThinking: (thinking) => {
    set(s => {
      const msgs = [...s.messages]
      const lastIdx = msgs.findLastIndex(m => m.role === 'assistant')
      if (lastIdx === -1) return {}
      // thinking 진입 시 기존 텍스트가 있으면 줄바꿈 삽입 (다음 턴 텍스트와 분리)
      const prev = msgs[lastIdx]
      const content = thinking && prev.content ? prev.content + '\n\n' : prev.content
      msgs[lastIdx] = { ...prev, content, thinking }
      return { messages: msgs }
    })
  },
}))
