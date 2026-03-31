import { useState } from 'react'
import { Eye, EyeOff, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import { useSettingsStore } from '@/store/settingsStore'

export default function SetupScreen() {
  const { validateApiKey, updateSettings, isSaving, isValidating } = useSettingsStore()

  const [apiKey, setApiKey]       = useState('')
  const [userName, setUserName]   = useState('')
  const [showKey, setShowKey]     = useState(false)
  const [step, setStep]           = useState('form')   // form | validating | saving | done | error
  const [errorMsg, setErrorMsg]   = useState('')

  const isLoading = isValidating || isSaving

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrorMsg('')

    if (!apiKey.trim()) {
      setErrorMsg('Anthropic API Key를 입력해 주세요.')
      return
    }
    if (!userName.trim()) {
      setErrorMsg('사용자 이름을 입력해 주세요.')
      return
    }

    // 1단계: API Key 검증
    setStep('validating')
    const validation = await validateApiKey(apiKey.trim())
    if (!validation.valid) {
      setStep('error')
      setErrorMsg(validation.message)
      return
    }

    // 2단계: 설정 저장
    setStep('saving')
    try {
      await updateSettings({
        anthropic_api_key: apiKey.trim(),
        user_name: userName.trim(),
      })
      setStep('done')
    } catch (err) {
      setStep('error')
      setErrorMsg(err?.data?.message || '설정 저장에 실패했습니다. 서버 연결을 확인해 주세요.')
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'var(--color-surface-50)' }}
    >
      <div
        className="w-full max-w-md rounded-2xl shadow-xl p-8 flex flex-col gap-6"
        style={{ background: 'var(--color-surface-0)', border: '1px solid var(--color-surface-200)' }}
      >
        {/* 헤더 */}
        <div className="flex flex-col gap-1">
          <h1 className="text-xl font-bold" style={{ color: 'var(--color-ink-900)' }}>
            AI 비서 시작하기
          </h1>
          <p className="text-sm" style={{ color: 'var(--color-ink-500)' }}>
            서비스를 이용하려면 아래 정보를 입력해 주세요.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Anthropic API Key */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: 'var(--color-ink-700)' }}>
              Anthropic API Key <span style={{ color: 'var(--color-danger-500)' }}>*</span>
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={e => { setApiKey(e.target.value); setStep('form'); setErrorMsg('') }}
                placeholder="sk-ant-..."
                disabled={isLoading || step === 'done'}
                className="w-full rounded-lg px-3 py-2 text-sm border outline-none transition-colors"
                style={{
                  background: 'var(--color-surface-100)',
                  borderColor: errorMsg && !userName ? 'var(--color-danger-500)' : 'var(--color-surface-300)',
                  color: 'var(--color-ink-900)',
                  paddingRight: '2.5rem',
                }}
              />
              <button
                type="button"
                onClick={() => setShowKey(v => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1"
                style={{ color: 'var(--color-ink-300)' }}
                tabIndex={-1}
              >
                {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
            <p className="text-xs" style={{ color: 'var(--color-ink-300)' }}>
              console.anthropic.com에서 발급한 키를 입력하세요.
            </p>
          </div>

          {/* 사용자 이름 */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: 'var(--color-ink-700)' }}>
              사용자 이름 <span style={{ color: 'var(--color-danger-500)' }}>*</span>
            </label>
            <input
              type="text"
              value={userName}
              onChange={e => { setUserName(e.target.value); setStep('form'); setErrorMsg('') }}
              placeholder="홍길동"
              disabled={isLoading || step === 'done'}
              className="w-full rounded-lg px-3 py-2 text-sm border outline-none transition-colors"
              style={{
                background: 'var(--color-surface-100)',
                borderColor: 'var(--color-surface-300)',
                color: 'var(--color-ink-900)',
              }}
            />
          </div>

          {/* 에러 메시지 */}
          {errorMsg && (
            <div
              className="flex items-start gap-2 rounded-lg px-3 py-2.5 text-sm"
              style={{ background: '#fef2f2', color: '#dc2626' }}
            >
              <AlertCircle size={14} className="mt-0.5 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* 진행 상태 메시지 */}
          {step === 'validating' && (
            <StatusRow color="var(--color-brand-600)" icon={<Loader2 size={14} className="animate-spin" />}>
              API Key를 검증하고 있습니다…
            </StatusRow>
          )}
          {step === 'saving' && (
            <StatusRow color="var(--color-brand-600)" icon={<Loader2 size={14} className="animate-spin" />}>
              설정을 저장하고 있습니다…
            </StatusRow>
          )}
          {step === 'done' && (
            <StatusRow color="#16a34a" icon={<CheckCircle2 size={14} />}>
              설정 완료! 잠시 후 시작됩니다.
            </StatusRow>
          )}

          {/* 제출 버튼 */}
          <button
            type="submit"
            disabled={isLoading || step === 'done'}
            className="w-full rounded-lg py-2.5 text-sm font-semibold text-white transition-opacity mt-1"
            style={{
              background: 'var(--color-brand-600)',
              opacity: isLoading || step === 'done' ? 0.6 : 1,
              cursor: isLoading || step === 'done' ? 'not-allowed' : 'pointer',
            }}
          >
            {isLoading ? '처리 중…' : step === 'done' ? '완료' : '시작하기'}
          </button>
        </form>
      </div>
    </div>
  )
}

function StatusRow({ icon, color, children }) {
  return (
    <div className="flex items-center gap-2 text-sm" style={{ color }}>
      {icon}
      <span>{children}</span>
    </div>
  )
}
