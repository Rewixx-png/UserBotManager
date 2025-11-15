# file: userbot_logic/userbot.py

import logging
import re
import html as html_lib
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import AuthKeyUnregisteredError

from database.db_manager import db_get_account_details, db_delete_account

# ID сервисного аккаунта Telegram
TELEGRAM_SERVICE_ID = 777000

async def get_account_info(user_id: int, phone: str) -> str:
    """Подключается к аккаунту и возвращает строку с информацией о нём в HTML."""
    details = await db_get_account_details(user_id, phone)
    if not details:
        return "❌ Не удалось найти данные для этого аккаунта."

    api_id, api_hash, session_string = details
    info_text = ""

    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise AuthKeyUnregisteredError

        me = await client.get_me()
        info_text = (
            f"<b>ℹ️ Информация об аккаунте <code>{me.phone}</code></b>\n\n"
            f"<b>ID:</b> <code>{me.id}</code>\n"
            f"<b>Имя:</b> {me.first_name or 'Нет'}\n"
            f"<b>Фамилия:</b> {me.last_name or 'Нет'}\n"
            f"<b>Юзернейм:</b> <code>@{me.username or 'Нет'}</code>\n"
            f"<b>Premium:</b> {'Да' if me.premium else 'Нет'}"
        )
    except AuthKeyUnregisteredError:
        info_text = "❌ <b>Ошибка:</b> Сессия была аннулирована. Пожалуйста, удалите и добавьте аккаунт заново."
        await db_delete_account(user_id, phone)
    except Exception as e:
        logging.error(f"Ошибка при получении информации: {e}")
        info_text = f"❌ Произошла неизвестная ошибка при подключении: {e}"
    finally:
        if client.is_connected():
            await client.disconnect()
    
    return info_text


async def check_session_validity(session_string: str, api_id: int, api_hash: str) -> bool:
    """Быстро проверяет, действительна ли сессия, не сбрасывая её."""
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    is_valid = False
    try:
        await client.connect()
        if await client.is_user_authorized():
            is_valid = True
    except Exception as e:
        logging.warning(f"Ошибка проверки сессии: {e}")
        is_valid = False
    finally:
        if client.is_connected():
            await client.disconnect()
            
    return is_valid


async def get_last_service_messages(user_id: int, phone: str) -> str:
    """Подключается к аккаунту и извлекает только строки с кодами из последних 5 сообщений."""
    details = await db_get_account_details(user_id, phone)
    if not details:
        return "❌ Не удалось найти данные для этого аккаунта."

    api_id, api_hash, session_string = details
    
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise AuthKeyUnregisteredError

        messages = await client.get_messages(TELEGRAM_SERVICE_ID, limit=5)

        if not messages:
            return "Кодов от Telegram (777000) не найдено."

        formatted_codes = []
        for msg in messages:
            extracted_line = None
            # Ищем нужную строку в тексте сообщения
            for line in msg.text.splitlines():
                if "Код для входа" in line:
                    extracted_line = line
                    break
            
            # Если нашли строку, форматируем её
            if extracted_line:
                # Безопасно преобразуем **...** в <b>...</b>, экранируя остальной текст
                parts = re.split(r'(\*\*.*?\*\*)', extracted_line)
                processed_parts = []
                for part in parts:
                    if part.startswith('**') and part.endswith('**'):
                        content = part[2:-2]
                        processed_parts.append(f"<b>{html_lib.escape(content)}</b>")
                    else:
                        processed_parts.append(html_lib.escape(part))
                
                message_html = "".join(processed_parts)
            else:
                # Запасной вариант, если формат сообщения изменился
                message_html = "<i>Не удалось извлечь строку с кодом из этого сообщения.</i>"

            # Добавляем отформатированную строку и время
            formatted_codes.append(
                f"<code>{msg.date.strftime('%H:%M:%S')}</code> — {message_html}"
            )
        
        header = f"<b>Последние {len(messages)} кодов от Telegram (777000):</b>\n\n"
        return header + "\n".join(formatted_codes)

    except AuthKeyUnregisteredError:
        return "❌ <b>Ошибка:</b> Сессия недействительна. Пожалуйста, перезайдите в аккаунт."
    except Exception as e:
        logging.error(f"Ошибка при получении сообщений: {e}")
        return f"❌ Произошла ошибка при получении сообщений: {e}"
    finally:
        if client.is_connected():
            await client.disconnect()