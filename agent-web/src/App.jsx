import { useEffect } from 'react'
import './index.css'
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'
import ChatWindow from '@/components/chat/ChatWindow'
import FileExplorer from '@/components/files/FileExplorer'
import SettingsPanel from '@/components/settings/SettingsPanel'
import SetupScreen from '@/components/setup/SetupScreen'
import { useUiStore } from '@/store/uiStore'
import { useSettingsStore } from '@/store/settingsStore'

export default function App() {
  const { view } = useUiStore()
  const { isInitialized, fetchSettings } = useSettingsStore()

  // 앱 최초 마운트 시 설정 조회 → 초기화 여부 판단
  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  // 아직 초기화 여부를 모르는 경우 (서버 응답 대기)
  if (isInitialized === null) {
    return (
      <div className="flex h-screen items-center justify-center" style={{ background: 'var(--color-surface-50)' }}>
        <div
          className="w-6 h-6 rounded-full border-2 animate-spin"
          style={{ borderColor: 'var(--color-brand-500)', borderTopColor: 'transparent' }}
        />
      </div>
    )
  }

  // API Key 또는 사용자명 미설정 → 초기 설정 화면
  if (!isInitialized) {
    return <SetupScreen />
  }

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--color-surface-50)' }}>
      {/* LNB 사이드바 */}
      <Sidebar />

      {/* 메인 영역 */}
      <div
        className="flex flex-col overflow-hidden"
        style={{
          flex: '0 1 var(--chat-max-w)',
          minWidth: '320px',
          margin: '0 auto',
        }}
      >
        {/* 헤더 */}
        <Header />

        {/* 콘텐츠 */}
        {view === 'chat'     && <ChatWindow />}
        {view === 'files'    && <FileExplorer />}
        {view === 'settings' && <SettingsRedirect />}
      </div>

      {/* 설정 모달 (헤더 아이콘 / 사이드바 버튼으로 열림) */}
      <SettingsPanel />
    </div>
  )
}

// 사이드바 설정 버튼 → 모달 자동 오픈
function SettingsRedirect() {
  const { openSettings, setView } = useUiStore()
  useEffect(() => {
    openSettings()
    setView('chat')
  }, [openSettings, setView])
  return null
}
