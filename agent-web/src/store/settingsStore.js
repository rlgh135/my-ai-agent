import { create } from 'zustand'
import * as settingsApi from '@/api/settings'

export const useSettingsStore = create((set) => ({
  settings: {},
  isLoading: false,
  isSaving: false,

  fetchSettings: async () => {
    set({ isLoading: true })
    try {
      const data = await settingsApi.getSettings()
      set({ settings: data })
    } finally {
      set({ isLoading: false })
    }
  },

  updateSettings: async (patch) => {
    set({ isSaving: true })
    try {
      const data = await settingsApi.patchSettings(patch)
      set({ settings: data })
    } finally {
      set({ isSaving: false })
    }
  },

  setLocal: (patch) => set(s => ({ settings: { ...s.settings, ...patch } })),
}))
