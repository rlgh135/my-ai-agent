"""웹 검색 API (API-016)"""
from fastapi import APIRouter
from app.mcp.search import web_search
from app.schemas.search import SearchRequest, SearchOut

router = APIRouter()


@router.post("/search", response_model=SearchOut)
async def search(body: SearchRequest):
    return await web_search(body.query, body.limit)
