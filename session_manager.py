import asyncio
import os
import sys
from pathlib import Path
from telethon import TelegramClient, errors
from telethon.tl.functions.account import UpdateStatusRequest
from termcolor import colored


API_ID = 
API_HASH = "-"
SESSIONS_DIR = Path("sessions")

def ensure_sessions_dir():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

async def create_new_session():
    print(colored("\n=== СОЗДАНИЕ НОВОЙ СЕССИИ ===\n", "cyan"))
    phone = input(colored("Введите номер телефона (в формате +79991234567): ", "yellow")).strip()
    if not phone:
        print(colored("Номер не введён. Отмена.", "red"))
        return None

    session_name = input(colored("Введите имя сессии (без расширения, например acc1): ", "yellow")).strip()
    if not session_name:
        session_name = f"session_{phone[-8:]}"
        print(colored(f"Имя не введено, использую {session_name}", "green"))

    session_path = SESSIONS_DIR / f"{session_name}.session"
    if session_path.exists():
        overwrite = input(colored("Сессия с таким именем уже существует. Перезаписать? (y/n): ", "red")).lower()
        if overwrite != 'y':
            print(colored("Отмена.", "yellow"))
            return None

    client = TelegramClient(str(session_path), API_ID, API_HASH)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            code = input(colored("Введите код из Telegram: ", "yellow")).strip()
            try:
                await client.sign_in(phone, code)
            except errors.SessionPasswordNeededError:
                password = input(colored("Включена двухфакторная аутентификация. Введите пароль: ", "yellow")).strip()
                await client.sign_in(password=password)
        me = await client.get_me()
        print(colored(f"\n✅ Сессия успешно создана и авторизована как {me.first_name} (@{me.username})", "green"))
        return session_path
    except errors.FloodWaitError as e:
        print(colored(f"❌ Флуд-вейт: подождите {e.seconds} секунд.", "red"))
        return None
    except Exception as e:
        print(colored(f"❌ Ошибка авторизации: {e}", "red"))
        return None
    finally:
        await client.disconnect()

async def check_session(session_path: Path) -> bool:
    try:
        client = TelegramClient(str(session_path), API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            print(colored(f"   [НЕ АВТОРИЗОВАНА] {session_path.name}", "red"))
            return False
        me = await client.get_me()
    
        await client(UpdateStatusRequest(offline=False))
        print(colored(f"   [РАБОТАЕТ] {session_path.name} – {me.first_name} (@{me.username})", "green"))
        return True
    except errors.FloodWaitError as e:
        print(colored(f"   [ФЛУД] {session_path.name} – ожидание {e.seconds} сек", "yellow"))
        return False
    except (errors.AuthKeyError, errors.SessionRevokedError, errors.PhoneNumberBannedError) as e:
        print(colored(f"   [НЕ РАБОТАЕТ] {session_path.name} – {type(e).name}", "red"))
        return False
    except Exception as e:
        print(colored(f"   [ОШИБКА] {session_path.name} – {str(e)[:70]}", "red"))
        return False
    finally:
        await client.disconnect()

async def check_all_sessions():
    ensure_sessions_dir()
    session_files = list(SESSIONS_DIR.glob("*.session"))
    if not session_files:
        print(colored("Нет ни одного .session файла в папке sessions/", "yellow"))
        return

    print(colored(f"\n=== ПРОВЕРКА {len(session_files)} СЕССИЙ ===\n", "cyan"))
    working = 0
    for s in session_files:
        if await check_session(s):
            working += 1
        await asyncio.sleep(0.5)  
    print(colored(f"\nИтог: {working}/{len(session_files)} сессий работоспособны.", "green" if working else "red"))

async def test_single_session():
    name = input(colored("Введите имя файла сессии (без .session): ", "yellow")).strip()
    if not name:
        return
    session_path = SESSIONS_DIR / f"{name}.session"
    if not session_path.exists():
        print(colored(f"Файл {session_path} не найден.", "red"))
        return
    await check_session(session_path)

async def main_menu():
    ensure_sessions_dir()
    while True:
        print(colored("\n════════════════════════════════════", "blue"))
        print(colored("   МЕНЕДЖЕР СЕССИЙ TELEGRAM", "white", attrs=['bold']))
        print(colored("════════════════════════════════════", "blue"))
        print("1. Создать новую сессию (авторизация)")
        print("2. Проверить все сессии в папке sessions/")
        print("3. Проверить одну конкретную сессию")
        print("4. Выйти")
        choice = input(colored("Выберите действие (1-4): ", "yellow")).strip()
        if choice == '1':
            await create_new_session()
        elif choice == '2':
            await check_all_sessions()
        elif choice == '3':
            await test_single_session()
        elif choice == '4':
            print(colored("Выход.", "cyan"))
            break
        else:
            print(colored("Неверный выбор.", "red"))

if __name__ == "__main__":
    asyncio.run(main_menu())