from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class AppSetting(Base):
    """Key-value 설정 테이블. 민감 값은 Vault로 암호화."""
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    is_encrypted: Mapped[bool] = mapped_column(default=False)
