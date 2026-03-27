import api from './client'

export const listSessions   = ()          => api.get('/sessions')
export const createSession  = (body)      => api.post('/sessions', body)
export const getMessages    = (sessionId) => api.get(`/sessions/${sessionId}`)
export const deleteSession  = (sessionId) => api.delete(`/sessions/${sessionId}`)
