from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os

# Асинхронная БД SQLite
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./project_manager.db"

# Создаем асинхронный движок
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Включаем логирование SQL запросов для отладки
)

# Создаем асинхронную сессию
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

# Функция для получения сессии БД
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()