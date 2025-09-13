# sensory_data_client/repositories/pg_repositoryAuth.py
from __future__ import annotations
import hashlib, secrets
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional

from sqlalchemy import select, update, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sensory_data_client.db.base import get_session
from sensory_data_client.db.auth.refresh_token_orm import RefreshTokenORM
from sensory_data_client.exceptions import DatabaseError

def _hash(raw: str) -> str:
    return hashlib.sha256((raw or "").encode("utf-8")).hexdigest()

class RefreshTokenRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._sf = session_factory

    async def mint(
        self,
        user_id: UUID,
        *,
        ttl_days: int = 60,
        user_agent: str | None = None,
        ip_address: str | None = None,
        device_label: str | None = None,
    ) -> str:
        raw = secrets.token_urlsafe(48)
        h = _hash(raw)
        now = datetime.now(timezone.utc)
        rt = RefreshTokenORM(
            user_id=user_id,
            token_hash=h,
            expires_at=now + timedelta(days=max(1, ttl_days)),
            user_agent=(user_agent or "")[:255] or None,
            ip_address=(ip_address or "")[:64] or None,
            device_label=(device_label or "")[:100] or None,
        )
        async with get_session(self._sf) as s:
            try:
                s.add(rt)
                await s.commit()
                return raw
            except SQLAlchemyError as e:
                await s.rollback()
                raise DatabaseError(f"mint refresh failed: {e}") from e

    async def rotate_with_user(
        self,
        old_raw: str,
        *,
        ttl_days: int = 60,
        user_agent: str | None = None,
        ip_address: str | None = None,
        device_label: str | None = None,
    ) -> Optional[Tuple[UUID, str]]:
        """
        Возвращает (user_id, new_refresh_raw) или None, если невозможно.
        Атомарно: помечает старый токен отозванным и создает новый.
        """
        old_h = _hash(old_raw)
        async with get_session(self._sf) as s:
            try:
                # SELECT ... FOR UPDATE, чтобы избежать гонок при одновременной ротации
                q = (
                    select(RefreshTokenORM)
                    .where(
                        RefreshTokenORM.token_hash == old_h,
                        RefreshTokenORM.revoked == False,
                        RefreshTokenORM.expires_at > func.now(),
                    )
                    .with_for_update(skip_locked=True)
                )
                row = (await s.execute(q)).scalar_one_or_none()
                if not row:
                    await s.rollback()
                    return None

                # Создаем новый токен
                new_raw = secrets.token_urlsafe(48)
                new_h = _hash(new_raw)
                now = datetime.now(timezone.utc)
                new_rt = RefreshTokenORM(
                    user_id=row.user_id,
                    token_hash=new_h,
                    expires_at=now + timedelta(days=max(1, ttl_days)),
                    user_agent=(user_agent or "")[:255] or row.user_agent,
                    ip_address=(ip_address or "")[:64] or row.ip_address,
                    device_label=(device_label or "")[:100] or row.device_label,
                )
                s.add(new_rt)
                await s.flush()  # чтобы получить new_rt.id

                # Помечаем старый отозванным и связываем
                row.revoked = True
                row.replaced_by_id = new_rt.id
                row.last_used_at = now

                await s.commit()
                return (row.user_id, new_raw)
            except SQLAlchemyError as e:
                await s.rollback()
                raise DatabaseError(f"rotate refresh failed: {e}") from e

    async def revoke(self, raw: str) -> bool:
        h = _hash(raw)
        async with get_session(self._sf) as s:
            try:
                stmt = (
                    update(RefreshTokenORM)
                    .where(RefreshTokenORM.token_hash == h, RefreshTokenORM.revoked == False)
                    .values(revoked=True, last_used_at=datetime.now(timezone.utc))
                )
                res = await s.execute(stmt)
                await s.commit()
                return (res.rowcount or 0) > 0
            except SQLAlchemyError as e:
                await s.rollback()
                raise DatabaseError(f"revoke refresh failed: {e}") from e

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        async with get_session(self._sf) as s:
            try:
                stmt = (
                    update(RefreshTokenORM)
                    .where(RefreshTokenORM.user_id == user_id, RefreshTokenORM.revoked == False)
                    .values(revoked=True, last_used_at=datetime.now(timezone.utc))
                )
                res = await s.execute(stmt)
                await s.commit()
                return int(res.rowcount or 0)
            except SQLAlchemyError as e:
                await s.rollback()
                raise DatabaseError(f"revoke all refresh failed: {e}") from e

    async def purge_expired(self, limit: int = 1000) -> int:
        """
        Опционально — удалить (или пометить) протухшие токены.
        """
        from sqlalchemy import delete
        async with get_session(self._sf) as s:
            try:
                stmt = (
                    delete(RefreshTokenORM)
                    .where(RefreshTokenORM.expires_at <= func.now())
                )
                # Примечание: не все БД поддерживают RETURNING для delete, поэтому возвращаем 0/кол-во эвристически
                res = await s.execute(stmt)
                await s.commit()
                return int(res.rowcount or 0)
            except SQLAlchemyError as e:
                await s.rollback()
                raise DatabaseError(f"purge expired refresh failed: {e}") from e