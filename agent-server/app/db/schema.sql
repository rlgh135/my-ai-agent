-- =============================================================================
-- AI Agent Server — PostgreSQL DDL
-- Database: agent_db
-- Version : 1.0.0
-- Updated : 2026-03-27
-- =============================================================================
-- 실행 방법
--   psql -U <user> -d agent_db -f schema.sql
--
-- 사전 준비
--   CREATE DATABASE agent_db ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8';
--   CREATE USER agent_user WITH PASSWORD 'your_password';
--   GRANT ALL PRIVILEGES ON DATABASE agent_db TO agent_user;
--   \c agent_db
--   GRANT ALL ON SCHEMA public TO agent_user;
-- =============================================================================

-- pgcrypto 확장 (gen_random_uuid 사용, PostgreSQL 14 미만 환경)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. chat_sessions — 대화 세션
-- =============================================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    title        VARCHAR(255) NOT NULL    DEFAULT '새 대화',
    message_count INTEGER     NOT NULL    DEFAULT 0
                              CHECK (message_count >= 0),
    created_at   TIMESTAMPTZ  NOT NULL    DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL    DEFAULT NOW()
);

COMMENT ON TABLE  chat_sessions                IS '대화 세션 목록';
COMMENT ON COLUMN chat_sessions.id             IS '세션 UUID (PK)';
COMMENT ON COLUMN chat_sessions.title          IS '세션 제목 (최초 메시지에서 자동 생성)';
COMMENT ON COLUMN chat_sessions.message_count  IS '누적 메시지 수';
COMMENT ON COLUMN chat_sessions.created_at     IS '생성 시각 (UTC)';
COMMENT ON COLUMN chat_sessions.updated_at     IS '최종 갱신 시각 (UTC)';

-- updated_at 자동 갱신 트리거 함수
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at
    ON chat_sessions (created_at DESC);

-- =============================================================================
-- 2. messages — 대화 메시지
-- =============================================================================
CREATE TABLE IF NOT EXISTS messages (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID        NOT NULL
                            REFERENCES chat_sessions (id)
                            ON DELETE CASCADE
                            ON UPDATE CASCADE,
    role        VARCHAR(20) NOT NULL
                            CHECK (role IN ('user', 'assistant', 'tool')),
    content     TEXT        NOT NULL    DEFAULT '',
    msg_type    VARCHAR(30) NOT NULL    DEFAULT 'text'
                            CHECK (msg_type IN (
                                'text',
                                'tool_use',
                                'tool_result',
                                'task_pending'
                            )),
    created_at  TIMESTAMPTZ NOT NULL    DEFAULT NOW()
);

COMMENT ON TABLE  messages             IS '대화 메시지 (사용자 / AI / 도구)';
COMMENT ON COLUMN messages.id         IS '메시지 UUID (PK)';
COMMENT ON COLUMN messages.session_id IS '소속 세션 (FK → chat_sessions.id, CASCADE)';
COMMENT ON COLUMN messages.role       IS '발화자 역할: user | assistant | tool';
COMMENT ON COLUMN messages.content    IS '메시지 본문 (마크다운 또는 JSON 직렬화 문자열)';
COMMENT ON COLUMN messages.msg_type   IS '메시지 유형: text | tool_use | tool_result | task_pending';
COMMENT ON COLUMN messages.created_at IS '생성 시각 (UTC)';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_messages_session_id
    ON messages (session_id, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_messages_created_at
    ON messages (created_at DESC);

-- =============================================================================
-- 3. app_settings — 애플리케이션 설정 (Key-Value)
-- =============================================================================
CREATE TABLE IF NOT EXISTS app_settings (
    key          VARCHAR(100) PRIMARY KEY,
    value        TEXT         NOT NULL DEFAULT '',
    is_encrypted BOOLEAN      NOT NULL DEFAULT FALSE,
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  app_settings              IS 'Key-Value 형태의 앱 설정. 민감 값은 Fernet 암호화 저장.';
COMMENT ON COLUMN app_settings.key          IS '설정 키 (PK)';
COMMENT ON COLUMN app_settings.value        IS '설정 값 (암호화된 경우 Fernet 토큰)';
COMMENT ON COLUMN app_settings.is_encrypted IS 'TRUE이면 value가 Fernet 암호화 상태';
COMMENT ON COLUMN app_settings.updated_at   IS '최종 갱신 시각 (UTC)';

CREATE OR REPLACE TRIGGER trg_app_settings_updated_at
    BEFORE UPDATE ON app_settings
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 기본 설정값 삽입 (없을 경우에만)
INSERT INTO app_settings (key, value, is_encrypted) VALUES
    ('claude_model',        'claude-3-5-sonnet-20241022', FALSE),
    ('claude_max_tokens',   '8192',                       FALSE),
    ('search_provider',     'brave',                      FALSE),
    ('task_timeout_seconds','300',                        FALSE),
    ('smtp_host',           '',                           FALSE),
    ('smtp_port',           '587',                        FALSE),
    ('smtp_user',           '',                           FALSE),
    ('smtp_password',       '',                           TRUE ),
    ('smtp_from',           '',                           FALSE),
    ('brave_api_key',       '',                           TRUE ),
    ('anthropic_api_key',   '',                           TRUE )
ON CONFLICT (key) DO NOTHING;

-- =============================================================================
-- 권한 부여 (agent_user 사용 시)
-- =============================================================================
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO agent_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO agent_user;
