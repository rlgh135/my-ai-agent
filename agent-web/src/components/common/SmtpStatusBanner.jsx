import { useEffect, useState, useCallback } from 'react'
import { AlertTriangle, X, Settings } from 'lucide-react'
import { getSmtpStatus } from '@/api/email'
import { useUiStore } from '@/store/uiStore'

/**
 * SmtpStatusBanner
 *
 * SMTP가 설정되지 않았거나 연결에 실패한 경우 채팅 화면 상단에 표시하는 경고 배너.
 * - not_configured / auth_failed / fail → 배너 표시
 * - ok → 배너 숨김
 * - 닫기 버튼(X)을 누르면 해당 세션 동안 배너를 숨긴다.
 */
export default function SmtpStatusBanner() {
  const { openSettings } = useUiStore()
  const [status, setStatus] = useState(null)   // null | SmtpStatusOut
  const [dismissed, setDismissed] = useState(false)

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getSmtpStatus()
      setStatus(data)
    } catch {
      // smtp-status 조회 실패는 무시 — 다른 기능에 영향 없음
    }
  }, [])

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  // 배너 표시 조건 판단
  const shouldShow =
    !dismissed &&
    status !== null &&
    status.test_result !== 'ok'

  if (!shouldShow) return null

  const { title, description } = resolveCopy(status)

  return (
    <div
      role="alert"
      className="flex items-start gap-3 px-4 py-3 text-sm border-b"
      style={{
        background: 'var(--color-warning-50, #fffbeb)',
        borderColor: 'var(--color-warning-200, #fde68a)',
        color: 'var(--color-warning-800, #92400e)',
      }}
    >
      {/* 아이콘 */}
      <AlertTriangle size={16} className="shrink-0 mt-0.5" style={{ color: 'var(--color-warning-500, #f59e0b)' }} />

      {/* 메시지 */}
      <div className="flex-1 min-w-0">
        <span className="font-semibold">{title}</span>
        {' '}
        <span style={{ color: 'var(--color-warning-700, #b45309)' }}>{description}</span>
        {' '}
        <button
          onClick={openSettings}
          className="underline font-medium hover:opacity-80 transition-opacity"
          style={{ color: 'var(--color-brand-600)' }}
        >
          설정 열기
          <Settings size={11} className="inline ml-0.5 mb-0.5" />
        </button>
      </div>

      {/* 닫기 */}
      <button
        onClick={() => setDismissed(true)}
        aria-label="배너 닫기"
        className="shrink-0 p-0.5 rounded hover:opacity-70 transition-opacity"
        style={{ color: 'var(--color-warning-500, #f59e0b)' }}
      >
        <X size={14} />
      </button>
    </div>
  )
}

/** test_result 값에 따른 표시 문구 */
function resolveCopy(status) {
  switch (status.test_result) {
    case 'not_configured':
      return {
        title: '이메일 기능이 비활성화되어 있습니다.',
        description: 'SMTP 설정이 없어 이메일 전송을 사용할 수 없습니다.',
      }
    case 'auth_failed':
      return {
        title: 'SMTP 인증에 실패했습니다.',
        description: '계정 또는 앱 비밀번호가 올바르지 않습니다.',
      }
    case 'fail':
      return {
        title: 'SMTP 서버에 연결할 수 없습니다.',
        description: status.error ? `오류: ${status.error}` : '호스트·포트 설정을 확인해 주세요.',
      }
    default:
      return {
        title: 'SMTP 상태 확인 필요.',
        description: '이메일 설정을 확인해 주세요.',
      }
  }
}
