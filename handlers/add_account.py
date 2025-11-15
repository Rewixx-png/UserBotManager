# file: handlers/add_account.py

import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

# Импорты Telethon
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PasswordHashInvalidError,
    PhoneNumberUnoccupiedError
)

from config import API_ID, API_HASH
from database.db_manager import db_save_account
from keyboards.inline_kb import get_main_menu_kb

router = Router()

# Упрощенная машина состояний. Шаги для API ID и HASH уже удалены.
class AddAccount(StatesGroup):
    phone = State()
    code = State()
    password = State()

# Этот хендлер теперь сразу запрашивает номер телефона
@router.callback_query(F.data == "add_account")
async def cq_add_account_start(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text(
        "Начинаем добавление нового аккаунта.\n\n"
        "Пожалуйста, введите **номер телефона** в международном формате (например, +79123456789).",
        parse_mode="Markdown"
    )
    # Сразу переходим к состоянию ввода телефона
    await state.set_state(AddAccount.phone)
    await query.answer()


@router.message(AddAccount.phone)
async def process_phone(message: Message, state: FSMContext):
    await message.answer("⏳ Отправляю код... Пожалуйста, подождите.")
    phone = message.text

    # Создаем клиент Telethon в памяти с новой сессией
    client = TelegramClient(StringSession(), API_ID, API_HASH)

    try:
        await client.connect()
        sent_code = await client.send_code_request(phone)

        # Сохраняем в состояние нужные данные для следующего шага
        await state.update_data(
            phone=phone,
            phone_code_hash=sent_code.phone_code_hash,
            session_string=client.session.save()  # Сохраняем сессию как строку
        )

        await message.answer("Вам был отправлен код в Telegram. Пожалуйста, введите его:")
        await state.set_state(AddAccount.code)

    except Exception as e:
        logging.error(f"Ошибка на этапе отправки кода: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}\n\nПопробуйте добавить аккаунт еще раз.")
        await state.clear()
    finally:
        # Отключаемся и будем переподключаться на следующем шаге, используя сессию
        if client.is_connected():
            await client.disconnect()


@router.message(AddAccount.code)
async def process_code(message: Message, state: FSMContext):
    code = message.text
    data = await state.get_data()
    phone = data['phone']

    # Восстанавливаем клиент из строки сессии
    client = TelegramClient(StringSession(data.get('session_string')), API_ID, API_HASH)

    try:
        await client.connect()
        # Входим, используя код
        await client.sign_in(phone, code, phone_code_hash=data['phone_code_hash'])

        # Если вход успешен без 2FA пароля
        final_session_string = client.session.save()
        await db_save_account(message.from_user.id, phone, API_ID, API_HASH, final_session_string)

        await message.answer("✅ Аккаунт успешно добавлен!", reply_markup=get_main_menu_kb())
        await state.clear()

    except SessionPasswordNeededError:
        # Если нужен 2FA пароль
        # Обновляем строку сессии, так как она могла измениться
        await state.update_data(session_string=client.session.save())
        await message.answer("Этот аккаунт защищен облачным паролем (2FA). Введите пароль:")
        await state.set_state(AddAccount.password)

    except PhoneCodeInvalidError:
        await message.answer("Неверный код. Начните заново.", reply_markup=get_main_menu_kb())
        await state.clear()
    except PhoneNumberUnoccupiedError:
        await message.answer("Этот номер телефона не зарегистрирован. Начните заново.", reply_markup=get_main_menu_kb())
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка на этапе ввода кода: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}\n\nНачните заново.", reply_markup=get_main_menu_kb())
        await state.clear()
    finally:
        if client.is_connected():
            await client.disconnect()


@router.message(AddAccount.password)
async def process_password(message: Message, state: FSMContext):
    password = message.text
    data = await state.get_data()
    phone = data['phone']

    # Восстанавливаем клиент из строки сессии
    client = TelegramClient(StringSession(data.get('session_string')), API_ID, API_HASH)

    try:
        await client.connect()
        # Входим, используя пароль
        await client.sign_in(password=password)

        final_session_string = client.session.save()
        await db_save_account(message.from_user.id, phone, API_ID, API_HASH, final_session_string)

        await message.answer("✅ Аккаунт успешно добавлен!", reply_markup=get_main_menu_kb())
        await state.clear()

    except PasswordHashInvalidError:
        await message.answer("Неверный пароль. Начните заново.", reply_markup=get_main_menu_kb())
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка на этапе ввода пароля: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}\n\nНачните заново.", reply_markup=get_main_menu_kb())
        await state.clear()
    finally:
        if client.is_connected():
            await client.disconnect()