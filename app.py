# file: app.py

import asyncio
import logging
from aiogram import Bot, Dispatcher

# Импортируем конфигурацию
from config import BOT_TOKEN

# Импортируем роутеры из handlers
from handlers import common, add_account

# Импортируем функцию для инициализации БД
from database.db_manager import db_start

async def main():
    """Основная функция для запуска бота."""
    logging.basicConfig(level=logging.INFO)

    # Инициализируем базу данных
    await db_start()

    # Создаем объекты бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Включаем роутеры в главный диспетчер
    dp.include_router(common.router)
    dp.include_router(add_account.router)

    # Удаляем вебхук, если он был установлен ранее
    await bot.delete_webhook(drop_pending_updates=True)

    print("Бот запущен...")
    # Запускаем поллинг
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())