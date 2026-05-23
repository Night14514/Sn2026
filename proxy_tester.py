import asyncio
import random
import string
import time
from pathlib import Path
from telethon import TelegramClient
from termcolor import colored

# Ваши API данные (можно использовать те же, что и в основном скрипте)
API_ID = -
API_HASH = "-"
TEST_PHONE = "+79123456789"  # Номер для теста (можно фейковый, главное – не существующий)
TIMEOUT = 5  # секунд на подключение
MAX_PROXIES_TO_TEST = 500   # лимит, чтобы не грузить сеть

def load_proxies_from_file(file_path="proxy_list.txt"):
    if not Path(file_path).exists():
        return []
    with open(file_path, "r") as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return proxies[:MAX_PROXIES_TO_TEST]

def parse_proxy(proxy_str):
    """
    Преобразует строку прокси в кортеж для Telethon:
    Поддерживает:
      - ip:port
      - user:pass@ip:port
      - socks5://ip:port
      - http://ip:port
    Возвращает (type, host, port, username, password)
    """
    original = proxy_str
    # Убираем протокол, если указан
    if proxy_str.startswith('socks5://'):
        proxy_str = proxy_str[9:]
    elif proxy_str.startswith('socks4://'):
        proxy_str = proxy_str[9:]
    elif proxy_str.startswith('http://'):
        proxy_str = proxy_str[7:]
    elif proxy_str.startswith('https://'):
        proxy_str = proxy_str[8:]
    
    username = password = None
    if '@' in proxy_str:
        auth, proxy_str = proxy_str.split('@', 1)
        if ':' in auth:
            username, password = auth.split(':', 1)
        else:
            username = auth
    
    if ':' not in proxy_str:
        return None
    host, port_str = proxy_str.split(':', 1)
    # порт может быть с лишними символами
    if not port_str.isdigit():
        import re
        match = re.search(r'\d+', port_str)
        if match:
            port_str = match.group()
        else:
            return None
    port = int(port_str)
    # По умолчанию используем SOCKS5 (Telethon предпочитает его для надёжности)
    # Если нужно принудительно HTTP, можно вернуть ('http', ...)
    return ('socks5', host, port, username, password)

async def test_proxy(proxy_str, api_id, api_hash, test_phone):
    """Проверяет один прокси: пытается подключиться и отправить запрос кода."""
    proxy_tuple = parse_proxy(proxy_str)
    if proxy_tuple is None:
        return False, "Invalid format"
    
    session_name = ''.join(random.choices(string.ascii_lowercase, k=8))
    client = None
    start = time.time()
    try:
        client = TelegramClient(session_name, api_id, api_hash, proxy=proxy_tuple, timeout=TIMEOUT)
        await client.connect()
        if not await client.is_user_authorized():
            # Пытаемся отправить запрос кода (это требует минимального подключения)
            # Если прокси блокирует отправку кода, но соединение прошло – всё равно считаем рабочим
            await client.send_code_request(test_phone)
        elapsed = (time.time() - start) * 1000
        return True, f"OK ({elapsed:.0f} ms)"
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        error_msg = str(e).split('\n')[0][:80]
        return False, f"FAIL ({elapsed:.0f} ms) – {error_msg}"
    finally:
        if client:
            await client.disconnect()
        # Удаляем временную сессию
        import os
        try:
            os.remove(session_name + ".session")
        except:
            pass

async def mass_test():
    print(colored("\n=== ТЕСТИРОВАНИЕ ПРОКСИ ДЛЯ TELEGRAM (TELEPHONE) ===\n", "cyan"))
    proxies = load_proxies_from_file()
    if not proxies:
        print(colored("Файл proxy_list.txt не найден или пуст.", "red"))
        return
    
    print(colored(f"Найдено прокси: {len(proxies)}. Начинаем проверку...\n", "yellow"))
    working = []
    failed = []
    
    for idx, proxy in enumerate(proxies, 1):
        print(f"[{idx}/{len(proxies)}] Тестируем {proxy}...", end=" ", flush=True)
        ok, msg = await test_proxy(proxy, API_ID, API_HASH, TEST_PHONE)
        if ok:
            print(colored(msg, "green"))
            working.append(proxy)
        else:
            print(colored(msg, "red"))
            failed.append(proxy)
        # маленькая задержка между тестами, чтобы не перегружать сеть
        await asyncio.sleep(0.5)
    
    # Вывод статистики
    print(colored("\n=== РЕЗУЛЬТАТЫ ===\n", "cyan"))
    print(colored(f"Рабочих: {len(working)}", "green"))
    print(colored(f"Нерабочих: {len(failed)}", "red"))
    
    if working:
        with open("working_proxies.txt", "w") as f:
            f.write("\n".join(working))
        print(colored("\n✅ Рабочие прокси сохранены в working_proxies.txt", "green"))
    else:
        print(colored("\n❌ Нет ни одного рабочего прокси. Удалите или очистите proxy_list.txt, чтобы атака кодами шла без прокси.", "yellow"))

if __name__ == "__main__":
    asyncio.run(mass_test())