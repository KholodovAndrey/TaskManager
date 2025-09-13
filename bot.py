import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from handlers import main_menu, projects, tasks, expenses, statistics
from middlewares.db import DatabaseMiddleware
from services.database import Base, engine

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создание таблиц БД
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Инициализация бота и диспетчера с новым синтаксисом
bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключение middleware
dp.update.middleware(DatabaseMiddleware())

# Подключение роутеров
dp.include_router(main_menu.router)
dp.include_router(projects.router)
dp.include_router(tasks.router)
dp.include_router(expenses.router)
dp.include_router(statistics.router)

# Запуск бота
async def main():
    await create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())