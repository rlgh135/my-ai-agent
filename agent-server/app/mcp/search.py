"""웹 검색 MCP 래퍼 — Brave Search API (폴백: DuckDuckGo)"""
import httpx
from app.core.config import settings


async def web_search(query: str, limit: int = 5) -> dict:
    if settings.SEARCH_PROVIDER == "brave" and settings.BRAVE_API_KEY:
        return await _brave_search(query, limit)
    return await _duckduckgo_search(query, limit)


async def _brave_search(query: str, limit: int) -> dict:
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
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
    return {"query": query, "results": results, "total": len(results)}


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
                "title": topic.get("Text", "")[:80],
                "url": topic.get("FirstURL", ""),
                "snippet": topic.get("Text", ""),
            })
    return {"query": query, "results": results, "total": len(results)}
