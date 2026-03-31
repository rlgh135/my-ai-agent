import api from './client'

export const getTokenUsage = (sessionId) =>
  api.get(`/chat/token-usage?session_id=${encodeURIComponent(sessionId)}`)
