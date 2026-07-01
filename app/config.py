import os
from sqlalchemy import select
from app.database import async_session
from app.models import User

DEFAULT_PASSWORD = "123456"
DEFAULT_SERVER = "s5"


async def get_or_create_user(username: str) -> User:
    """Get existing user or auto-create with defaults (password=123456, empty api_key)."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                username=username,
                password=DEFAULT_PASSWORD,
                api_key=os.getenv("OTPK_instanAPI_KEY", ""),
                server=DEFAULT_SERVER,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def get_user(username: str) -> User | None:
    """Get user by username, or None if not found."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()


async def update_user(username: str, **kwargs) -> User | None:
    """Update user fields (password, api_key, server)."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key) and value:
                    setattr(user, key, value)
            await session.commit()
            await session.refresh(user)
        return user
