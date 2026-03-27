"""토큰 사용량 계산 (tiktoken 사용, 실패 시 문자 수 기반 근사)"""
import tiktoken
from app.core.config import settings


_ENCODING_CACHE: dict[str, tiktoken.Encoding] = {}


def _get_encoding(model: str) -> tiktoken.Encoding:
    if model not in _ENCODING_CACHE:
        try:
            _ENCODING_CACHE[model] = tiktoken.encoding_for_model(model)
        except KeyError:
            _ENCODING_CACHE[model] = tiktoken.get_encoding("cl100k_base")
    return _ENCODING_CACHE[model]


def count_tokens(text: str, model: str | None = None) -> int:
    model = model or settings.CLAUDE_MODEL
    try:
        enc = _get_encoding(model)
        return len(enc.encode(text))
    except Exception:
        # 폴백: 문자 수 / 3.5 근사
        return max(1, int(len(text) / 3.5))


def count_messages_tokens(messages: list[dict]) -> int:
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += count_tokens(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and "text" in block:
                    total += count_tokens(block["text"])
    return total


MAX_TOKENS = {
    "claude-3-5-sonnet-20241022": 200_000,
    "claude-3-opus-20240229":     200_000,
    "claude-3-haiku-20240307":    200_000,
}


def get_usage_status(used: int, model: str | None = None) -> dict:
    model = model or settings.CLAUDE_MODEL
    max_t = MAX_TOKENS.get(model, 200_000)
    pct = round(used / max_t * 100, 1)
    if pct >= 91:
        status = "danger"
    elif pct >= 71:
        status = "warning"
    else:
        status = "normal"
    return {"used_tokens": used, "max_tokens": max_t, "usage_percent": pct, "status": status}
