import { tokenStatusColor, tokenStatusBg } from '@/utils/formatters'

export default function TokenBadge({ usage }) {
  const { status, usagePercent, usedTokens, maxTokens } = usage
  const pct = Math.min(usagePercent, 100)

  return (
    <div className="flex items-center gap-2 text-[11px]">
      {/* 수치 텍스트 */}
      <span className={`font-semibold ${tokenStatusColor(status)}`}>
        {(usedTokens / 1000).toFixed(0)}k / {(maxTokens / 1000).toFixed(0)}k
      </span>

      {/* 게이지 바 */}
      <div
        className="w-20 h-1.5 rounded-full overflow-hidden"
        style={{ background: 'var(--color-surface-200)' }}
        title={`컨텍스트 사용량 ${pct.toFixed(0)}%`}
      >
        <div
          className={`h-full rounded-full transition-all duration-500 ${tokenStatusBg(status)}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* 위험 상태 경고 표시 */}
      {status === 'danger' && (
        <span className="text-[10px] font-medium px-1.5 py-0.5 rounded" style={{ background: '#fef2f2', color: 'var(--color-danger-500)' }}>
          LIMIT
        </span>
      )}
    </div>
  )
}
