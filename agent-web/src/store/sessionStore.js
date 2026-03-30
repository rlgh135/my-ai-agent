import { create } from 'zustand'
import * as sessionApi from '@/api/sessions'

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
      // 백엔드 응답: { sessions: [...], total: N }
      set({ sessions: Array.isArray(data) ? data : (data.sessions ?? []) })
    } finally {
      set({ isLoadingSessions: false })
    }
  },

  createSession: async (title = '새 대화') => {
    const session = await sessionApi.createSession({ title })
    set(s => ({ sessions: [session, ...s.sessions], activeSessionId: session.id, messages: [] }))
    return session
  },

  selectSession: async (sessionId) => {
    if (get().activeSessionId === sessionId) return
    set({ activeSessionId: sessionId, messages: [], isLoadingMessages: true })
    try {
      const data = await sessionApi.getMessages(sessionId)
      // 백엔드 응답: { session_id: '...', messages: [...] }
      set({ messages: Array.isArray(data) ? data : (data.messages ?? []) })
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
      msgs[lastIdx] = { ...msgs[lastIdx], content, streaming: false }
      return { messages: msgs }
    })
  },
}))
