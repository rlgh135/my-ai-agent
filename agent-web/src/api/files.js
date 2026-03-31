import api from './client'

export const listDirectory = (path)  => api.get(`/files?path=${encodeURIComponent(path)}`)
export const readFile      = (path)  => api.get(`/files/content?path=${encodeURIComponent(path)}`)
export const createFile    = (body)  => api.post('/files', body)
export const updateFile    = (body)  => api.put('/files', body)
export const backupFile    = (body)  => api.post('/files/backup', body)
export const deleteFile    = (path)  => api.delete('/files', { body: JSON.stringify({ path }) })
