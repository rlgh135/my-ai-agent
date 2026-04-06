"""POST /api/tasks/{id}/approve|reject — 작업 협의 카드 (API-007~008)"""
from fastapi import APIRouter
from app.core.exceptions import TaskNotFoundError, TaskTimeoutError
from app.core.logger import get_task_logger
from app.schemas.chat import TaskResult
import asyncio

router = APIRouter()
task_log = get_task_logger()

# ── 인메모리 pending task 저장소 ───────────────────────────────────────────────
# { task_id: { "type": str, "params": dict, "future": asyncio.Future, "timeout_task": Task } }
_pending: dict = {}

TIMEOUT_SECONDS = 300  # 5분


def register_task(task_id: str, task_type: str, params: dict) -> asyncio.Future:
    """협의 카드 생성 시 호출 — Future를 반환하여 백엔드 로직이 승인을 기다림"""
    loop = asyncio.get_running_loop()   # Python 3.10+: get_event_loop() 대신 사용
    future = loop.create_future()

    async def _timeout():
        await asyncio.sleep(TIMEOUT_SECONDS)
        if not future.done():
            task_log.warning("TIMEOUT | task_id=%s | type=%s", task_id, task_type)
            future.set_exception(TaskTimeoutError(task_id))
            _pending.pop(task_id, None)

    timeout_task = asyncio.create_task(_timeout())
    _pending[task_id] = {"type": task_type, "params": params, "future": future, "timeout_task": timeout_task}
    task_log.info("REGISTER | task_id=%s | type=%s | path=%s",
                  task_id, task_type, params.get("path", ""))
    return future


@router.post("/tasks/{task_id}/approve", response_model=TaskResult)
async def approve_task(task_id: str):
    entry = _pending.pop(task_id, None)
    if not entry:
        task_log.warning("APPROVE FAIL | task_id=%s | not found in _pending", task_id)
        raise TaskNotFoundError(task_id)
    entry["timeout_task"].cancel()
    future: asyncio.Future = entry["future"]
    if not future.done():
        future.set_result("approved")
    task_log.info("APPROVE | task_id=%s | type=%s", task_id, entry["type"])
    return TaskResult(task_id=task_id, status="approved", message="작업이 승인되어 실행됩니다.")


@router.post("/tasks/{task_id}/reject", response_model=TaskResult)
async def reject_task(task_id: str):
    entry = _pending.pop(task_id, None)
    if not entry:
        task_log.warning("REJECT FAIL  | task_id=%s | not found in _pending", task_id)
        raise TaskNotFoundError(task_id)
    entry["timeout_task"].cancel()
    future: asyncio.Future = entry["future"]
    if not future.done():
        future.set_result("rejected")
    task_log.info("REJECT  | task_id=%s | type=%s", task_id, entry["type"])
    return TaskResult(task_id=task_id, status="rejected", message="작업이 취소되었습니다.")
