#!/bin/bash
# 최초 개발환경 세팅 스크립트
set -e

echo "=== AI Agent Server 개발환경 세팅 ==="

# Python 버전 확인
python3 --version

# 가상환경 생성
if [ ! -d ".venv" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv .venv
fi

# 활성화
source .venv/bin/activate

# 패키지 설치
echo "📥 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements-dev.txt

# .env 파일 생성
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ .env 파일 생성 완료. ANTHROPIC_API_KEY를 설정하세요."
fi

# data 폴더 생성
mkdir -p data

echo ""
echo "✅ 세팅 완료!"
echo "   1. .env 파일에서 ANTHROPIC_API_KEY를 설정하세요."
echo "   2. bash scripts/start.sh 로 서버를 실행하세요."
echo "   3. http://localhost:8000/docs 에서 API 문서를 확인하세요."
