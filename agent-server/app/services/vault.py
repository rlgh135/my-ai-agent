"""Vault — 민감 정보 암호화/복호화 (Fernet)"""
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    key = settings.VAULT_KEY
    if not key:
        # 최초 실행 시 키 자동 생성 후 .env에 저장
        key = Fernet.generate_key().decode()
        _append_env("VAULT_KEY", key)
        # Pydantic v2 BaseSettings는 기본적으로 frozen이므로
        # object.__setattr__으로 우회해 런타임 값만 갱신한다.
        # (재시작 시 .env에서 읽어 오므로 영속성 문제 없음)
        object.__setattr__(settings, "VAULT_KEY", key)
    return Fernet(key.encode() if isinstance(key, str) else key)


def _append_env(name: str, value: str) -> None:
    env_path = ".env"
    try:
        with open(env_path, "a") as f:
            f.write(f"\n{name}={value}\n")
    except OSError:
        # .env 파일을 쓸 수 없어도 런타임 키는 사용 가능 (재시작 시 재생성)
        pass


def encrypt(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
