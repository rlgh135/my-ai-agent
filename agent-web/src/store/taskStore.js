import { create } from 'zustand'
import * as taskApi from '@/api/tasks'

export const useTaskStore = create((set, get) => ({
  pendingTasks: [],   // { id, type, description, payload, createdAt }
  taskHistory: [],

  addPendingTask: (task) => {
    set(s => ({ pendingTasks: [...s.pendingTasks, task] }))
  },

  approveTask: async (taskId) => {
    await taskApi.approveTask(taskId)
    set(s => {
      const task = s.pendingTasks.find(t => t.id === taskId)
      return {
        pendingTasks: s.pendingTasks.filter(t => t.id !== taskId),
        taskHistory: task ? [{ ...task, status: 'approved', resolvedAt: new Date().toISOString() }, ...s.taskHistory] : s.taskHistory,
      }
    })
  },

  rejectTask: async (taskId) => {
    await taskApi.rejectTask(taskId)
    set(s => {
      const task = s.pendingTasks.find(t => t.id === taskId)
      return {
        pendingTasks: s.pendingTasks.filter(t => t.id !== taskId),
        taskHistory: task ? [{ ...task, status: 'rejected', resolvedAt: new Date().toISOString() }, ...s.taskHistory] : s.taskHistory,
      }
    })
  },

  clearHistory: () => set({ taskHistory: [] }),
}))
