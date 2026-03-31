"""웹 검색 MCP 래퍼 — Naver / Brave / DuckDuckGo"""
import httpx
from app.core.config import settings


async def web_search(query: str, limit: int = 5) -> dict:
    """언어 및 설정에 따라 적합한 검색 엔진을 자동 선택."""
    # 한국어 감지 (가나/한자 제외하고 한글 비율로 판단)
    korean_chars = sum(1 for c in query if '\uAC00' <= c <= '\uD7A3')
    is_korean = korean_chars / max(len(query), 1) > 0.3

    if is_korean and getattr(settings, "NAVER_API_KEY", ""):
        return await _naver_search(query, limit)
    if settings.BRAVE_API_KEY:
        return await _brave_search(query, limit)
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
        # Naver 실패 시 Brave 또는 DuckDuckGo로 폴백
        if settings.BRAVE_API_KEY:
            return await _brave_search(query, limit)
        return await _duckduckgo_search(query, limit)


async def _brave_search(query: str, limit: int) -> dict:
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept":              "application/json",
        "Accept-Encoding":     "gzip",
        "X-Subscription-Token": settings.BRAVE_API_KEY,
    }
    params = {"q": query, "count": min(limit, 10)}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
    results = [
        {"title": w.get("title", ""), "url": w.get("url", ""), "snippet": w.get("description", "")}
        for w in data.get("web", {}).get("results", [])[:limit]
    ]
    return {"query": query, "provider": "brave", "results": results, "total": len(results)}


async def _duckduckgo_search(query: str, limit: int) -> dict:
    """DuckDuckGo Instant Answer API (무료, 제한적)"""
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    results = []
    for topic in data.get("RelatedTopics", [])[:limit]:
        if "Text" in topic:
            results.append({
                "title":   topic.get("Text", "")[:80],
                "url":     topic.get("FirstURL", ""),
                "snippet": topic.get("Text", ""),
            })
    return {"query": query, "provider": "duckduckgo", "results": results, "total": len(results)}
