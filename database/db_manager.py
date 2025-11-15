# file: database/db_manager.py

import aiosqlite
from config import DB_NAME

async def db_start():
    """Инициализирует базу данных и создает таблицу, если она не существует."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                user_id INTEGER NOT NULL,
                phone TEXT NOT NULL,
                api_id INTEGER NOT NULL,
                api_hash TEXT NOT NULL,
                session_string TEXT NOT NULL,
                PRIMARY KEY (user_id, phone)
            );
        """)
        await db.commit()

async def db_save_account(user_id: int, phone: str, api_id: int, api_hash: str, session_string: str):
    """Сохраняет или обновляет данные аккаунта в БД."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO accounts (user_id, phone, api_id, api_hash, session_string) VALUES (?, ?, ?, ?, ?)",
            (user_id, phone, api_id, api_hash, session_string)
        )
        await db.commit()

async def db_get_user_accounts(user_id: int) -> list[str]:
    """Возвращает список телефонов всех аккаунтов пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT phone FROM accounts WHERE user_id = ?", (user_id,))
        return [row[0] for row in await cursor.fetchall()]

async def db_get_account_details(user_id: int, phone: str) -> tuple | None:
    """Возвращает детали конкретного аккаунта."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT api_id, api_hash, session_string FROM accounts WHERE user_id = ? AND phone = ?", (user_id, phone))
        return await cursor.fetchone()

async def db_delete_account(user_id: int, phone: str):
    """Удаляет аккаунт из БД."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM accounts WHERE user_id = ? AND phone = ?", (user_id, phone))
        await db.commit()