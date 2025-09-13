# sensory_data_client/db/auth/refresh_token_orm.py
from __future__ import annotations
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from ..base import Base, CreatedAt

class RefreshTokenORM(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)  # sha256
    created_at: Mapped[CreatedAt]
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user = relationship("UserORM")
    __table_args__ = (UniqueConstraint("token_hash", name="uq_refresh_token_hash"),)