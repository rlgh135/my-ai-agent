"""웹 검색 MCP 래퍼 — Naver / DuckDuckGo"""
import asyncio
import logging

import httpx
from duckduckgo_search import DDGS

from app.core.config import settings

logger = logging.getLogger(__name__)


async def web_search(query: str, limit: int = 5) -> dict:
    """언어 및 설정에 따라 적합한 검색 엔진을 자동 선택."""
    # 한국어 감지 (한글 비율로 판단)
    korean_chars = sum(1 for c in query if '\uAC00' <= c <= '\uD7A3')
    is_korean = korean_chars / max(len(query), 1) > 0.3

    if is_korean and getattr(settings, "NAVER_API_KEY", ""):
        return await _naver_search(query, limit)
    return await _duckduckgo_search(query, limit)


async def _naver_search(query: str, limit: int) -> dict:
    """Naver 검색 API (국문 검색)"""
    url = "https://openapi.naver.com/v1/search/webkr.json"
    headers = {
        "X-Naver-Client-Id":     settings.NAVER_CLIENT_ID if hasattr(settings, "NAVER_CLIENT_ID") else "",
        "X-Naver-Client-Secret": settings.NAVER_API_KEY,
    }
    params = {"query": query, "display": min(limit, 10), "sort": "sim"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
        results = [
            {
                "title":   item.get("title", "").replace("<b>", "").replace("</b>", ""),
                "url":     item.get("link", ""),
                "snippet": item.get("description", "").replace("<b>", "").replace("</b>", ""),
            }
            for item in data.get("items", [])[:limit]
        ]
        return {"query": query, "provider": "naver", "results": results, "total": len(results)}
    except Exception as exc:
        logger.warning("Naver 검색 실패, DuckDuckGo로 폴백: %s", exc)
        return await _duckduckgo_search(query, limit)


async def _duckduckgo_search(query: str, limit: int) -> dict:
    """DuckDuckGo 웹 검색 (API 키 불필요)"""
    def _sync_search():
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=limit))

    try:
        results_raw = await asyncio.get_event_loop().run_in_executor(None, _sync_search)
        results = [
            {
                "title":   r.get("title", ""),
                "url":     r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results_raw
        ]
        return {"query": query, "provider": "duckduckgo", "results": results, "total": len(results)}
    except Exception as exc:
        logger.error("DuckDuckGo 검색 실패: %s", exc)
        return {"query": query, "provider": "duckduckgo", "results": [], "total": 0, "error": str(exc)}
