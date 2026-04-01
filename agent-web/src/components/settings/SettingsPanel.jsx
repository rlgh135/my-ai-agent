import { useEffect, useState, useCallback } from 'react'
import {
  Save, Eye, EyeOff, CheckCircle2, Wifi, WifiOff,
  Loader2, AlertCircle, ShieldCheck, Search,
} from 'lucide-react'
import { useSettingsStore } from '@/store/settingsStore'
import { useUiStore } from '@/store/uiStore'
import Modal from '@/components/common/Modal'
import { getSmtpStatus } from '@/api/email'

// ── 필드 정의 ─────────────────────────────────────────────────────────────────
// allowed_directories는 별도 컴포넌트(DirectoriesField)로 처리
// anthropic_api_key / smtp_password / naver_api_key 는 서버에서 값을 내려주지 않음 (설정 여부만 반환)
// → 빈 채로 저장 시 서버는 기존 값 보존
const FIELD_DEFS = [
  {
    section: 'AI 모델',
    fields: [
      {
        key: 'claude_model',
        label: 'Claude 모델',
        type: 'text',
        placeholder: 'claude-sonnet-4-6',
      },
      {
        key: 'anthropic_api_key',
        label: 'Anthropic API Key',
        type: 'password',
        placeholder: 'sk-ant-...',
        configuredKey: 'anthropic_api_key_configured',  // 설정 여부 확인용 플래그 키
      },
    ],
  },
  {
    section: '이메일 (SMTP)',
    smtpSection: true,
    fields: [
      { key: 'smtp_host',     label: 'SMTP 호스트', type: 'text',     placeholder: 'smtp.gmail.com' },
      { key: 'smtp_port',     label: 'SMTP 포트',   type: 'number',   placeholder: '587' },
      { key: 'smtp_user',     label: 'SMTP 계정',   type: 'text',     placeholder: 'user@gmail.com' },
      { key: 'smtp_password', label: 'SMTP 비밀번호', type: 'password', placeholder: '변경하려면 새 비밀번호 입력' },
      { key: 'smtp_from',     label: '발신자 표시명', type: 'text',    placeholder: 'AI 비서 <user@gmail.com>' },
    ],
  },
  {
    section: '웹 검색',
    searchSection: true,
    fields: [
      {
        key: 'naver_client_id',
        label: 'Naver Client ID',
        type: 'text',
        placeholder: 'Naver Developers에서 발급 (한국어 검색용)',
      },
      {
        key: 'naver_api_key',
        label: 'Naver Client Secret',
        type: 'password',
        placeholder: '변경하려면 새 값 입력',
        configuredKey: 'naver_configured',
      },
    ],
  },
]

// ── 메인 컴포넌트 ──────────────────────────────────────────────────────────────
export default function SettingsPanel() {
  const { settingsPanelOpen, closeSettings } = useUiStore()
  const { settings, isLoading, isSaving, fetchSettings, updateSettings } = useSettingsStore()

  // 로컬 폼 상태: 서버 데이터 + 사용자 편집 내용
  const [form, setForm]     = useState({})
  const [dirText, setDirText] = useState('')   // allowed_directories textarea
  const [saved, setSaved]   = useState(false)
  const [error, setError]   = useState('')

  // 패널 열릴 때 서버에서 설정 조회 후 폼 초기화
  useEffect(() => {
    if (!settingsPanelOpen) return
    fetchSettings().then(() => {
      const s = useSettingsStore.getState().settings
      setForm(s)
      // allowed_directories: 배열 → 개행 구분 문자열
      const dirs = Array.isArray(s.allowed_directories) ? s.allowed_directories : []
      setDirText(dirs.join('\n'))
    })
  }, [settingsPanelOpen, fetchSettings])

  const handleChange = (key, val) => {
    setForm(f => ({ ...f, [key]: val }))
    setError('')
  }

  const handleSave = async () => {
    setError('')
    // allowed_directories: 개행 구분 → 배열 (빈 줄 제거)
    const dirs = dirText.split('\n').map(s => s.trim()).filter(Boolean)

    const patch = { ...form, allowed_directories: dirs }
    try {
      await updateSettings(patch)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setError(err?.data?.message || '저장에 실패했습니다.')
    }
  }

  return (
    <Modal open={settingsPanelOpen} onClose={closeSettings} title="설정" maxWidth="max-w-2xl">
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="animate-spin" size={20} style={{ color: 'var(--color-brand-500)' }} />
        </div>
      ) : (
        <div className="flex flex-col gap-6 max-h-[65vh] overflow-y-auto pr-1">

          {/* 사용자 정보 (읽기 전용) */}
          {settings.user_name && (
            <div
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm"
              style={{ background: 'var(--color-brand-50)', color: 'var(--color-brand-700)' }}
            >
              <ShieldCheck size={14} />
              <span><strong>{settings.user_name}</strong>님으로 인증되어 있습니다.</span>
            </div>
          )}

          {/* 섹션별 필드 */}
          {FIELD_DEFS.map(section => (
            <div key={section.section}>
              <h3
                className="text-xs font-semibold uppercase tracking-wider mb-3"
                style={{ color: 'var(--color-ink-500)' }}
              >
                {section.section}
              </h3>
              <div className="flex flex-col gap-3">
                {section.fields.map(field => (
                  <FieldRow
                    key={field.key}
                    field={field}
                    value={form[field.key] ?? ''}
                    isConfigured={field.configuredKey ? Boolean(settings[field.configuredKey]) : undefined}
                    onChange={val => handleChange(field.key, val)}
                  />
                ))}
                {section.smtpSection  && <SmtpTestRow />}
                {section.searchSection && <SearchStatusRow settings={settings} />}
              </div>
            </div>
          ))}

          {/* 파일 시스템 — 허용 디렉토리 */}
          <div>
            <h3
              className="text-xs font-semibold uppercase tracking-wider mb-3"
              style={{ color: 'var(--color-ink-500)' }}
            >
              파일 시스템
            </h3>
            <DirectoriesField value={dirText} onChange={setDirText} />
          </div>

        </div>
      )}

      {/* 에러 */}
      {error && (
        <div
          className="flex items-center gap-2 mt-3 px-3 py-2 rounded-lg text-sm"
          style={{ background: '#fef2f2', color: '#dc2626' }}
        >
          <AlertCircle size={13} />
          {error}
        </div>
      )}

      {/* 저장 버튼 */}
      <div
        className="flex justify-end mt-4 pt-4 border-t"
        style={{ borderColor: 'var(--color-surface-200)' }}
      >
        <button
          onClick={handleSave}
          disabled={isSaving || isLoading}
          className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-medium text-white transition-colors"
          style={{
            background: saved ? '#16a34a' : 'var(--color-brand-600)',
            opacity: isSaving || isLoading ? 0.6 : 1,
          }}
        >
          {saved ? (
            <><CheckCircle2 size={14} /> 저장됨</>
          ) : isSaving ? (
            <><Loader2 size={14} className="animate-spin" /> 저장 중…</>
          ) : (
            <><Save size={14} /> 저장</>
          )}
        </button>
      </div>
    </Modal>
  )
}

// ── 허용 디렉토리 (textarea, 한 줄에 하나) ─────────────────────────────────────
function DirectoriesField({ value, onChange }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-medium" style={{ color: 'var(--color-ink-700)' }}>
        허용 디렉토리
        <span className="ml-1.5 font-normal" style={{ color: 'var(--color-ink-300)' }}>
          (한 줄에 하나씩 절대 경로 입력)
        </span>
      </label>
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        rows={3}
        placeholder={'/Users/me/projects\nC:\\Users\\me\\documents'}
        className="w-full rounded-lg px-3 py-2 text-sm border outline-none font-mono resize-y"
        style={{
          background: 'var(--color-surface-100)',
          borderColor: 'var(--color-surface-300)',
          color: 'var(--color-ink-900)',
          minHeight: '72px',
        }}
      />
      <p className="text-xs" style={{ color: 'var(--color-ink-300)' }}>
        AI가 지정된 경로 하위의 파일에만 접근할 수 있습니다. 비워두면 모든 경로 허용.
      </p>
    </div>
  )
}

// ── 검색 상태 표시 ─────────────────────────────────────────────────────────────
function SearchStatusRow({ settings }) {
  if (settings.naver_configured) {
    return (
      <div
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs"
        style={{ background: '#f0fdf4', color: '#16a34a' }}
      >
        <Search size={12} />
        <span>한국어: Naver / 영문: DuckDuckGo</span>
      </div>
    )
  }

  return (
    <div
      className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs"
      style={{ background: 'var(--color-surface-100)', color: 'var(--color-ink-500)' }}
    >
      <Search size={12} />
      <span>DuckDuckGo 사용 중 (기본값) · 한국어 검색 강화: Naver API 설정</span>
    </div>
  )
}

// ── SMTP 연결 테스트 ───────────────────────────────────────────────────────────
function SmtpTestRow() {
  const [testing, setTesting] = useState(false)
  const [result, setResult]   = useState(null)

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
        {testing ? <Loader2 size={12} className="animate-spin" /> : <Wifi size={12} />}
        연결 테스트
      </button>
      {result && <SmtpStatusBadge result={result} />}
    </div>
  )
}

function SmtpStatusBadge({ result }) {
  const styles = {
    ok:             { icon: <CheckCircle2 size={11} />, label: '연결 성공',  bg: '#f0fdf4', fg: '#15803d' },
    auth_failed:    { icon: <WifiOff size={11} />,      label: '인증 실패',  bg: '#fef2f2', fg: '#dc2626' },
    fail:           { icon: <WifiOff size={11} />,      label: '연결 실패',  bg: '#fef2f2', fg: '#dc2626' },
    not_configured: { icon: <AlertCircle size={11} />,  label: '설정 필요',  bg: '#fffbeb', fg: '#b45309' },
  }
  const { icon, label, bg, fg } = styles[result.test_result] ?? styles.not_configured

  return (
    <span className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium" style={{ background: bg, color: fg }}>
      {icon}
      {label}
      {result.error && (
        <span title={result.error} className="ml-0.5 cursor-help opacity-70">
          <AlertCircle size={11} />
        </span>
      )}
    </span>
  )
}

// ── 개별 필드 ──────────────────────────────────────────────────────────────────
function FieldRow({ field, value, isConfigured, onChange }) {
  const [show, setShow] = useState(false)
  const isPassword = field.type === 'password'

  // 비밀번호 필드이고 이미 서버에 설정된 경우: 비어있어도 placeholder로 상태 표시
  const placeholder = isConfigured
    ? '● ● ● ● ● ● ● (변경하려면 새 값 입력)'
    : (field.placeholder ?? '')

  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium" style={{ color: 'var(--color-ink-700)' }}>
        {field.label}
        {isConfigured === true && (
          <span
            className="ml-2 px-1.5 py-0.5 rounded text-[10px] font-semibold"
            style={{ background: '#f0fdf4', color: '#16a34a' }}
          >
            설정됨
          </span>
        )}
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
          {field.options.map(opt => {
            const { value: optVal, label: optLabel } = typeof opt === 'string'
              ? { value: opt, label: opt }
              : opt
            return <option key={optVal} value={optVal}>{optLabel}</option>
          })}
        </select>
      ) : (
        <div className="relative">
          <input
            type={isPassword && !show ? 'password' : 'text'}
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder}
            className="w-full rounded-lg px-3 py-1.5 text-sm border outline-none transition-colors"
            style={{
              background: 'var(--color-surface-100)',
              borderColor: 'var(--color-surface-300)',
              color: 'var(--color-ink-900)',
              paddingRight: isPassword ? '2.5rem' : undefined,
            }}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShow(v => !v)}
              tabIndex={-1}
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
