import { create } from 'zustand'

export const useChatStore = create((set) => ({
  isStreaming: false,
  streamingContent: '',
  tokenUsage: {
    status: 'normal',   // normal | warning | danger
    usagePercent: 0,
    usedTokens: 0,
    maxTokens: 200000,
  },

  setStreaming: (val) => set({ isStreaming: val }),
  setStreamingContent: (content) => set({ streamingContent: content }),
  appendStreamingContent: (delta) =>
    set(s => ({ streamingContent: s.streamingContent + delta })),
  clearStreaming: () => set({ isStreaming: false, streamingContent: '' }),

  setTokenUsage: (usage) => set({ tokenUsage: usage }),
}))
