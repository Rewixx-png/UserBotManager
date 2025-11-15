# file: keyboards/inline_kb.py

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Tuple

def get_main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить аккаунт", callback_data="add_account"))
    builder.row(InlineKeyboardButton(text="📂 Мои аккаунты", callback_data="my_accounts"))
    return builder.as_markup()

def get_my_accounts_kb(accounts: List[Tuple[str, bool]]):
    builder = InlineKeyboardBuilder()
    for phone, is_valid in accounts:
        status_icon = "✅" if is_valid else "❌"
        builder.row(InlineKeyboardButton(text=f"{status_icon} {phone}", callback_data=f"select_account:{phone}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return builder.as_markup()

def get_account_actions_kb(phone: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="ℹ️ Информация", callback_data=f"info:{phone}"))
    # --- Новая кнопка ---
    builder.row(InlineKeyboardButton(text="✉️ Показать коды", callback_data=f"show_codes:{phone}"))
    builder.row(InlineKeyboardButton(text="📥 Выдать файл сессии", callback_data=f"export:{phone}"))
    builder.row(InlineKeyboardButton(text="❌ Удалить аккаунт", callback_data=f"delete:{phone}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="my_accounts"))
    return builder.as_markup()