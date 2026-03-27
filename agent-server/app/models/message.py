from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.db.database import Base
import uuid


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20))      # user | assistant | tool
    content: Mapped[str] = mapped_column(Text, default="")
    msg_type: Mapped[str] = mapped_column(
        String(30), default="text"
    )  # text | tool_use | tool_result | task_pending
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
