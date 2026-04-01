/**
 * 상대 시간 표시 (예: "방금 전", "3분 전", "어제")
 */
export function relativeTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  if (isNaN(date.getTime())) return ''
  const now = new Date()
  const diffMs = now - date
  const diffMin = Math.floor(diffMs / 60000)
  const diffHr = Math.floor(diffMs / 3600000)
  const diffDay = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return '방금 전'
  if (diffMin < 60) return `${diffMin}분 전`
  if (diffHr < 24) return `${diffHr}시간 전`
  if (diffDay === 1) return '어제'
  if (diffDay < 7) return `${diffDay}일 전`

  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
}

/**
 * 파일 크기 (bytes → 읽기 쉬운 단위)
 */
export function fileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`
}

/**
 * 토큰 사용량 상태에 따른 색상 클래스
 */
export function tokenStatusColor(status) {
  if (status === 'danger')  return 'text-danger-500'
  if (status === 'warning') return 'text-warning-400'
  return 'text-brand-500'
}

export function tokenStatusBg(status) {
  if (status === 'danger')  return 'bg-danger-500'
  if (status === 'warning') return 'bg-warning-400'
  return 'bg-brand-500'
}

/**
 * 파일 확장자 → 언어 (코드 하이라이팅용)
 */
export function extToLang(filename) {
  const ext = filename.split('.').pop()?.toLowerCase()
  const map = {
    js: 'javascript', jsx: 'jsx', ts: 'typescript', tsx: 'tsx',
    py: 'python', md: 'markdown', json: 'json', yaml: 'yaml',
    yml: 'yaml', html: 'html', css: 'css', sh: 'bash', sql: 'sql',
  }
  return map[ext] || 'text'
}
