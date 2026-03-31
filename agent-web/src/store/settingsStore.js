import { create } from 'zustand'
import * as settingsApi from '@/api/settings'

export const useSettingsStore = create((set) => ({
  settings: {},
  isLoading: false,
  isSaving: false,
  isValidating: false,
  /** true: API Key + 사용자명이 모두 설정된 상태 */
  isInitialized: null,  // null = 아직 확인 전

  fetchSettings: async () => {
    set({ isLoading: true })
    try {
      const data = await settingsApi.getSettings()
      const initialized = Boolean(data.anthropic_api_key_configured && data.user_name)
      set({ settings: data, isInitialized: initialized })
    } catch {
      // 서버 미응답 → 초기화 미완으로 간주
      set({ isInitialized: false })
    } finally {
      set({ isLoading: false })
    }
  },

  /**
   * Anthropic API Key 유효성을 서버에서 검증한다.
   * @returns {{ valid: boolean, message: string }}
   */
  validateApiKey: async (apiKey) => {
    set({ isValidating: true })
    try {
      const result = await settingsApi.validateApiKey(apiKey)
      return result
    } catch (err) {
      return { valid: false, message: err?.data?.message || '키 검증에 실패했습니다.' }
    } finally {
      set({ isValidating: false })
    }
  },

  updateSettings: async (patch) => {
    set({ isSaving: true })
    try {
      const result = await settingsApi.patchSettings(patch)
      // 저장 후 최신 설정 다시 조회
      const data = await settingsApi.getSettings()
      const initialized = Boolean(data.anthropic_api_key_configured && data.user_name)
      set({ settings: data, isInitialized: initialized })
      return result
    } finally {
      set({ isSaving: false })
    }
  },

  setLocal: (patch) => set(s => ({ settings: { ...s.settings, ...patch } })),
}))
