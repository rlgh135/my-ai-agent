from fastapi import HTTPException, status


class AgentException(HTTPException):
    """Base exception for agent-server."""


class PathNotAllowedError(AgentException):
    def __init__(self, path: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "PATH_NOT_ALLOWED", "message": f"허용되지 않은 경로입니다: {path}"},
        )


class AgentFileNotFoundError(AgentException):
    """파일을 찾을 수 없음 (404). Python built-in FileNotFoundError와 이름 충돌 방지."""
    def __init__(self, path: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"파일을 찾을 수 없습니다: {path}"},
        )


class AgentFileExistsError(AgentException):
    """동명 파일 충돌 (409). Python built-in FileExistsError와 이름 충돌 방지."""
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


class SmtpNotConfiguredError(AgentException):
    """SMTP 필수 항목(host/user/password)이 .env에 설정되지 않은 경우."""
    def __init__(self, missing: list[str] | None = None):
        missing_str = ", ".join(missing) if missing else "SMTP_HOST, SMTP_USER, SMTP_PASSWORD"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SMTP_NOT_CONFIGURED",
                "message": (
                    f"이메일 기능을 사용하려면 설정이 필요합니다. "
                    f"누락된 항목: {missing_str}. "
                    f"설정 패널에서 SMTP 정보를 입력해 주세요."
                ),
                "missing_fields": missing or ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"],
            },
        )


class SmtpUnavailableError(AgentException):
    """SMTP 설정은 있으나 서버 연결에 실패한 경우."""
    def __init__(self, detail: str = "SMTP 서버에 연결할 수 없습니다."):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SMTP_UNAVAILABLE",
                "message": detail,
                "hint": "SMTP 호스트/포트/계정 정보가 올바른지 설정 패널에서 확인해 주세요.",
            },
        )
