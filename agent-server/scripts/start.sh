#!/bin/bash
# 서버 실행 스크립트
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사합니다."
    cp .env.example .env
    echo "✅ .env 파일 생성 완료. ANTHROPIC_API_KEY를 설정 후 다시 실행하세요."
    exit 1
fi

# venv 활성화
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🚀 AI Agent Server 시작..."
uvicorn app.main:app \
    --host "${HOST:-127.0.0.1}" \
    --port "${PORT:-8000}" \
    --reload \
    --log-level info
