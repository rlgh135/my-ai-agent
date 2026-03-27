"""토큰 카운터 단위 테스트"""
from app.services.token_counter import count_tokens, get_usage_status


def test_count_tokens_basic():
    tokens = count_tokens("Hello, world!")
    assert tokens > 0


def test_get_usage_status_normal():
    result = get_usage_status(10_000)
    assert result["status"] == "normal"
    assert result["usage_percent"] < 70


def test_get_usage_status_warning():
    result = get_usage_status(160_000)
    assert result["status"] == "warning"


def test_get_usage_status_danger():
    result = get_usage_status(195_000)
    assert result["status"] == "danger"
