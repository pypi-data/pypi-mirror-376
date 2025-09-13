# sensory_data_client/repositories/pg_repositoryAuth.py
import hashlib, secrets
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sensory_data_client.db.base import get_session
from sensory_data_client.db.auth.refresh_token_orm import RefreshTokenORM
from sensory_data_client.exceptions import DatabaseError

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

class RefreshTokenRepository:
    def __init__(self, sf: async_sessionmaker[AsyncSession]):
        self._sf = sf

    async def mint(self, user_id, ttl_days: int = 60) -> str:
        raw = secrets.token_urlsafe(48)
        h = _hash(raw)
        now = datetime.now(timezone.utc)
        rt = RefreshTokenORM(user_id=user_id, token_hash=h, expires_at=now + timedelta(days=ttl_days))
        async with get_session(self._sf) as s:
            try:
                s.add(rt); await s.commit()
                return raw
            except SQLAlchemyError as e:
                await s.rollback(); raise DatabaseError(str(e))

    async def rotate(self, old_raw: str, ttl_days: int = 60) -> str | None:
        h = _hash(old_raw)
        async with get_session(self._sf) as s:
            q = await s.execute(select(RefreshTokenORM).where(RefreshTokenORM.token_hash == h, RefreshTokenORM.revoked == False))
            rt = q.scalar_one_or_none()
            if not rt or rt.expires_at < datetime.now(timezone.utc):
                return None
            # помечаем старый отозванным
            rt.revoked = True
            new_raw = secrets.token_urlsafe(48)
            new_h = _hash(new_raw)
            new_rt = RefreshTokenORM(user_id=rt.user_id, token_hash=new_h,
                                     expires_at=datetime.now(timezone.utc) + timedelta(days=ttl_days))
            s.add(new_rt)
            await s.commit()
            return new_raw