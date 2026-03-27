import { useEffect } from 'react'
import './index.css'
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'
import ChatWindow from '@/components/chat/ChatWindow'
import FileExplorer from '@/components/files/FileExplorer'
import SettingsPanel from '@/components/settings/SettingsPanel'
import { useUiStore } from '@/store/uiStore'

export default function App() {
  const { view, setView } = useUiStore()

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--color-surface-50)' }}>
      {/* LNB 사이드바 */}
      <Sidebar />

      {/* 메인 영역 */}
      <div className="flex flex-col flex-1 overflow-hidden">
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
