import { create } from 'zustand'

// 현재 활성화된 메인 뷰
// view: 'chat' | 'files' | 'settings'
export const useUiStore = create((set) => ({
  view: 'chat',
  sidebarCollapsed: false,
  settingsPanelOpen: false,

  setView: (view) => set({ view }),
  toggleSidebar: () => set(s => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  openSettings: () => set({ settingsPanelOpen: true }),
  closeSettings: () => set({ settingsPanelOpen: false }),
}))
