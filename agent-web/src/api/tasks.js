import api from './client'

export const approveTask = (taskId) => api.post(`/tasks/${taskId}/approve`)
export const rejectTask  = (taskId) => api.post(`/tasks/${taskId}/reject`)
