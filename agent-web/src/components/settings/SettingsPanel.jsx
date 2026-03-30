import { useEffect, useState, useCallback } from 'react'
import { Save, Eye, EyeOff, CheckCircle2, Wifi, WifiOff, Loader2, AlertCircle } from 'lucide-react'
import { useSettingsStore } from '@/store/settingsStore'
import { useUiStore } from '@/store/uiStore'
import Modal from '@/components/common/Modal'
import { getSmtpStatus } from '@/api/email'

const FIELD_DEFS = [
  {
    section: 'AI 모델',
    fields: [
      { key: 'claude_model',       label: 'Claude 모델',    type: 'text',     placeholder: 'claude-3-5-sonnet-20241022' },
      { key: 'anthropic_api_key',  label: 'Anthropic API Key', type: 'password', placeholder: 'sk-ant-...' },
    ],
  },
  {
    section: '파일 시스템',
    fields: [
      { key: 'allowed_directories', label: '허용 디렉토리', type: 'text', placeholder: 'C:/Users/User/projects' },
    ],
  },
  {
    section: '이메일 (SMTP)',
    smtpSection: true,   // SmtpTestRow 렌더링 트리거
    fields: [
      { key: 'smtp_host',    label: 'SMTP 호스트', type: 'text',     placeholder: 'smtp.gmail.com' },
      { key: 'smtp_port',    label: 'SMTP 포트',   type: 'number',   placeholder: '587' },
      { key: 'smtp_user',    label: 'SMTP 계정',   type: 'text',     placeholder: 'user@gmail.com' },
      { key: 'smtp_password',label: 'SMTP 암호',   type: 'password', placeholder: '앱 비밀번호' },
      { key: 'smtp_from',    label: '발신자 주소',  type: 'text',     placeholder: 'AI 비서 <user@gmail.com>' },
    ],
  },
  {
    section: '웹 검색',
    fields: [
      { key: 'search_provider', label: '검색 공급자', type: 'select', options: ['brave', 'duckduckgo'] },
      { key: 'brave_api_key',   label: 'Brave API Key', type: 'password', placeholder: 'BSA...' },
    ],
  },
]

export default function SettingsPanel() {
  const { settingsPanelOpen, closeSettings } = useUiStore()
  const { settings, isLoading, isSaving, fetchSettings, updateSettings, setLocal } = useSettingsStore()
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (settingsPanelOpen) fetchSettings()
  }, [settingsPanelOpen, fetchSettings])

  const handleSave = async () => {
    await updateSettings(settings)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <Modal open={settingsPanelOpen} onClose={closeSettings} title="설정" maxWidth="max-w-xl">
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin-slow w-6 h-6 rounded-full border-2"
            style={{ borderColor: 'var(--color-brand-500)', borderTopColor: 'transparent' }} />
        </div>
      ) : (
        <div className="flex flex-col gap-6 max-h-[60vh] overflow-y-auto pr-1">
          {FIELD_DEFS.map(section => (
            <SettingsSection
              key={section.section}
              section={section}
              settings={settings}
              onChange={(key, val) => setLocal({ [key]: val })}
            />
          ))}
        </div>
      )}

      {/* 저장 버튼 */}
      <div className="flex justify-end mt-4 pt-4 border-t" style={{ borderColor: 'var(--color-surface-200)' }}>
        <button
          onClick={handleSave}
          disabled={isSaving || isLoading}
          className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-medium text-white transition-colors"
          style={{ background: saved ? 'var(--color-success-500)' : 'var(--color-brand-600)' }}
        >
          {saved ? (
            <><CheckCircle2 size={14} /> 저장됨</>
          ) : isSaving ? (
            <><div className="animate-spin-slow w-3.5 h-3.5 rounded-full border-2 border-white border-t-transparent" /> 저장 중…</>
          ) : (
            <><Save size={14} /> 저장</>
          )}
        </button>
      </div>
    </Modal>
  )
}

function SettingsSection({ section, settings, onChange }) {
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--color-ink-500)' }}>
        {section.section}
      </h3>
      <div className="flex flex-col gap-3">
        {section.fields.map(field => (
          <FieldRow
            key={field.key}
            field={field}
            value={settings[field.key] ?? ''}
            onChange={(val) => onChange(field.key, val)}
          />
        ))}
        {/* SMTP 섹션에만 연결 테스트 행 추가 */}
        {section.smtpSection && <SmtpTestRow />}
      </div>
    </div>
  )
}

/** SMTP 연결 테스트 버튼 + 상태 배지 */
function SmtpTestRow() {
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState(null)   // null | SmtpStatusOut

  const handleTest = useCallback(async () => {
    setTesting(true)
    setResult(null)
    try {
      const data = await getSmtpStatus()
      setResult(data)
    } catch {
      setResult({ test_result: 'fail', error: '상태 조회 실패' })
    } finally {
      setTesting(false)
    }
  }, [])

  return (
    <div className="flex items-center gap-3 pt-1">
      {/* 연결 테스트 버튼 */}
      <button
        onClick={handleTest}
        disabled={testing}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors hover:opacity-80"
        style={{
          borderColor: 'var(--color-surface-300)',
          color: 'var(--color-ink-700)',
          background: 'var(--color-surface-100)',
        }}
      >
        {testing
          ? <Loader2 size={12} className="animate-spin" />
          : <Wifi size={12} />
        }
        연결 테스트
      </button>

      {/* 상태 배지 */}
      {result && <SmtpStatusBadge result={result} />}
    </div>
  )
}

/** 테스트 결과에 따른 인라인 배지 */
function SmtpStatusBadge({ result }) {
  const { icon, label, bg, fg } = resolveStyle(result.test_result)

  return (
    <span
      className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
      style={{ background: bg, color: fg }}
    >
      {icon}
      {label}
      {result.error && (
        <span
          title={result.error}
          className="ml-0.5 cursor-help"
          style={{ color: fg, opacity: 0.7 }}
        >
          <AlertCircle size={11} />
        </span>
      )}
    </span>
  )
}

function resolveStyle(testResult) {
  switch (testResult) {
    case 'ok':
      return {
        icon: <CheckCircle2 size={11} />,
        label: '연결 성공',
        bg: 'var(--color-success-50, #f0fdf4)',
        fg: 'var(--color-success-700, #15803d)',
      }
    case 'auth_failed':
      return {
        icon: <WifiOff size={11} />,
        label: '인증 실패',
        bg: 'var(--color-danger-50, #fef2f2)',
        fg: 'var(--color-danger-600, #dc2626)',
      }
    case 'fail':
      return {
        icon: <WifiOff size={11} />,
        label: '연결 실패',
        bg: 'var(--color-danger-50, #fef2f2)',
        fg: 'var(--color-danger-600, #dc2626)',
      }
    case 'not_configured':
    default:
      return {
        icon: <AlertCircle size={11} />,
        label: '설정 필요',
        bg: 'var(--color-warning-50, #fffbeb)',
        fg: 'var(--color-warning-700, #b45309)',
      }
  }
}

function FieldRow({ field, value, onChange }) {
  const [show, setShow] = useState(false)

  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium" style={{ color: 'var(--color-ink-700)' }}>
        {field.label}
      </label>

      {field.type === 'select' ? (
        <select
          value={value}
          onChange={e => onChange(e.target.value)}
          className="rounded-lg px-3 py-1.5 text-sm border outline-none"
          style={{
            background: 'var(--color-surface-100)',
            borderColor: 'var(--color-surface-300)',
            color: 'var(--color-ink-900)',
          }}
        >
          {field.options.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      ) : (
        <div className="relative">
          <input
            type={field.type === 'password' && !show ? 'password' : 'text'}
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={field.placeholder}
            className="w-full rounded-lg px-3 py-1.5 text-sm border outline-none"
            style={{
              background: 'var(--color-surface-100)',
              borderColor: 'var(--color-surface-300)',
              color: 'var(--color-ink-900)',
              paddingRight: field.type === 'password' ? '2.5rem' : undefined,
            }}
          />
          {field.type === 'password' && (
            <button
              type="button"
              onClick={() => setShow(v => !v)}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1"
              style={{ color: 'var(--color-ink-300)' }}
            >
              {show ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
