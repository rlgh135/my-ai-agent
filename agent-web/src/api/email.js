import api from './client'

/**
 * SMTP 연결 상태 조회 (GET /api/email/smtp-status)
 *
 * 반환 예시:
 *   { configured: false, host: '', port: 587, user: '', test_result: 'not_configured', missing_fields: [...] }
 *   { configured: true,  host: 'smtp.gmail.com', port: 587, user: '...', test_result: 'ok', missing_fields: [] }
 *   { configured: true,  ..., test_result: 'auth_failed', error: '...' }
 *   { configured: true,  ..., test_result: 'fail',        error: '...' }
 */
export async function getSmtpStatus() {
  return api.get('/email/smtp-status')
}

/**
 * 이메일 전송 요청 (POST /api/email/send)
 * — 실제 전송은 tasks/approve 후 실행되므로 202 협의 카드를 반환한다.
 *
 * SMTP 미설정 시 400 SmtpNotConfiguredError를 throw한다.
 * 에러 객체에는 data.missing_fields 배열이 포함될 수 있다.
 */
export async function sendEmailRequest({ to, subject, body, cc, attachments }) {
  return api.post('/email/send', { to, subject, body, cc, attachments })
}

/**
 * API 에러에서 SMTP 관련 사용자 메시지를 추출한다.
 *
 * @param {Error} err  client.js가 throw한 에러 (err.status, err.data 포함)
 * @returns {{ title: string, description: string, missingFields: string[], hint: string } | null}
 */
export function parseSmtpError(err) {
  if (!err?.data) return null

  const { code, message, missing_fields, hint } = err.data

  if (code === 'SMTP_NOT_CONFIGURED') {
    return {
      title: '이메일 설정이 필요합니다',
      description: message ?? 'SMTP 설정이 완료되지 않았습니다.',
      missingFields: missing_fields ?? [],
      hint: '설정 패널에서 SMTP 정보를 입력해 주세요.',
    }
  }

  if (code === 'SMTP_UNAVAILABLE') {
    return {
      title: 'SMTP 서버에 연결할 수 없습니다',
      description: message ?? 'SMTP 서버 연결에 실패했습니다.',
      missingFields: [],
      hint: hint ?? 'SMTP 호스트/포트/계정 정보가 올바른지 확인해 주세요.',
    }
  }

  return null
}
