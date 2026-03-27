from fastapi import HTTPException, status


class AgentException(HTTPException):
    """Base exception for agent-server."""


class PathNotAllowedError(AgentException):
    def __init__(self, path: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "PATH_NOT_ALLOWED", "message": f"허용되지 않은 경로입니다: {path}"},
        )


class FileNotFoundError(AgentException):
    def __init__(self, path: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"파일을 찾을 수 없습니다: {path}"},
        )


class FileExistsError(AgentException):
    def __init__(self, path: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "FILE_EXISTS", "message": f"동명 파일이 이미 존재합니다: {path}"},
        )


class SessionNotFoundError(AgentException):
    def __init__(self, session_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"세션을 찾을 수 없습니다: {session_id}"},
        )


class TaskNotFoundError(AgentException):
    def __init__(self, task_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"작업을 찾을 수 없습니다: {task_id}"},
        )


class TaskTimeoutError(AgentException):
    def __init__(self, task_id: str):
        super().__init__(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail={"code": "TASK_TIMEOUT", "message": "작업이 시간 초과로 취소되었습니다."},
        )


class LLMError(AgentException):
    def __init__(self, detail: str = "Claude API 호출 실패"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "LLM_ERROR", "message": detail},
        )


class SmtpUnavailableError(AgentException):
    def __init__(self, detail: str = "SMTP 서버에 연결할 수 없습니다."):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "SMTP_UNAVAILABLE", "message": detail},
        )
