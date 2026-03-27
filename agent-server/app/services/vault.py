"""SQLite Vault — 민감 정보 암호화/복호화 (Fernet)"""
from cryptography.fernet import Fernet
from app.core.config import settings
import base64
import os


def _get_fernet() -> Fernet:
    key = settings.VAULT_KEY
    if not key:
        # 최초 실행 시 키 자동 생성 후 .env에 저장
        key = Fernet.generate_key().decode()
        _append_env("VAULT_KEY", key)
        settings.VAULT_KEY = key
    return Fernet(key.encode() if isinstance(key, str) else key)


def _append_env(name: str, value: str) -> None:
    env_path = ".env"
    with open(env_path, "a") as f:
        f.write(f"\n{name}={value}\n")


def encrypt(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
