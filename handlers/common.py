# file: handlers/common.py
import os
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from telethon.sessions import StringSession, SQLiteSession

from keyboards.inline_kb import get_main_menu_kb, get_my_accounts_kb, get_account_actions_kb
from database.db_manager import db_get_user_accounts, db_delete_account, db_get_account_details
from userbot_logic.userbot import get_account_info, check_session_validity, get_last_service_messages

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("👋 Привет! Это бот для управления вашими Telegram-аккаунтами.", reply_markup=get_main_menu_kb())

@router.callback_query(F.data == "main_menu")
async def cq_main_menu(query: CallbackQuery):
    await query.message.edit_text("Главное меню:", reply_markup=get_main_menu_kb())
    await query.answer()

@router.callback_query(F.data == "my_accounts")
async def cq_my_accounts(query: CallbackQuery):
    await query.message.edit_text("⏳ Проверка аккаунтов, пожалуйста, подождите...")
    
    phones = await db_get_user_accounts(query.from_user.id)
    if not phones:
        await query.answer("У вас пока нет добавленных аккаунтов.", show_alert=True)
        await query.message.edit_text("Главное меню:", reply_markup=get_main_menu_kb())
        return

    accounts_with_status = []
    for phone in phones:
        details = await db_get_account_details(query.from_user.id, phone)
        if details:
            api_id, api_hash, session_string = details
            is_valid = await check_session_validity(session_string, api_id, api_hash)
            accounts_with_status.append((phone, is_valid))
        else:
            accounts_with_status.append((phone, False))

    await query.message.edit_text("Выберите аккаунт для управления:", reply_markup=get_my_accounts_kb(accounts_with_status))
    await query.answer()

@router.callback_query(F.data.startswith("select_account:"))
async def cq_select_account(query: CallbackQuery):
    phone = query.data.split(":")[1]
    await query.message.edit_text(f"Действия для аккаунта {phone}:", reply_markup=get_account_actions_kb(phone))

@router.callback_query(F.data.startswith("info:"))
async def cq_show_info(query: CallbackQuery):
    phone = query.data.split(":")[1]
    await query.answer("Подключаюсь, пожалуйста, подождите...", show_alert=False)
    
    info_text = await get_account_info(query.from_user.id, phone)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select_account:{phone}"))
    # --- ИЗМЕНЕНИЕ ---
    await query.message.edit_text(info_text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("delete:"))
async def cq_delete_account(query: CallbackQuery):
    phone = query.data.split(":")[1]
    await db_delete_account(query.from_user.id, phone)
    await query.answer("Аккаунт успешно удален!", show_alert=True)
    await cq_my_accounts(query)

@router.callback_query(F.data.startswith("export:"))
async def cq_export_session(query: CallbackQuery):
    phone = query.data.split(":")[1]
    await query.answer(f"Создаю файл сессии для {phone}...", show_alert=False)

    details = await db_get_account_details(query.from_user.id, phone)
    if not details:
        await query.message.answer("❌ Не удалось найти данные для этого аккаунта.")
        return

    _, _, session_string = details
    
    string_session = StringSession(session_string)
    session_filename = f"{query.from_user.id}_{phone}.session"
    sqlite_session = SQLiteSession(session_filename)
    
    sqlite_session.set_dc(string_session.dc_id, string_session.server_address, string_session.port)
    sqlite_session.auth_key = string_session.auth_key
    
    sqlite_session.save()
    sqlite_session.close()

    try:
        document = FSInputFile(session_filename)
        # --- ИЗМЕНЕНИЕ ---
        await query.message.answer_document(document, caption=f"Файл сессии для аккаунта <code>{phone}</code>", parse_mode="HTML")
    finally:
        if os.path.exists(session_filename):
            os.remove(session_filename)

@router.callback_query(F.data.startswith("show_codes:"))
async def cq_show_service_codes(query: CallbackQuery):
    phone = query.data.split(":")[1]
    await query.answer("Загружаю сообщения от Telegram...", show_alert=False)

    messages_text = await get_last_service_messages(query.from_user.id, phone)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select_account:{phone}"))
    
    # --- ИЗМЕНЕНИЕ ---
    await query.message.edit_text(messages_text, reply_markup=builder.as_markup(), parse_mode="HTML")