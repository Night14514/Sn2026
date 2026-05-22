import asyncio
import random
import aiohttp
import os
import re
from typing import Optional, Dict, List
from logger_utils import attack_logger
from config import API_ID, API_HASH, PROXY_FILE, SESSIONS_DIR


def parse_proxy(proxy_str: str):
    """Полностью совместимый парсер (SOCKS5, HTTP, MTProto)"""
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

def load_proxy_list():
    if os.path.exists("proxy_list.txt"):
        with open("proxy_list.txt", "r") as f:
            proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return proxies
    return []


async def check_proxy(proxy_str: str) -> bool:
    if not proxy_str:
        return False
    if proxy_str.startswith('mtproto://'):
        return True
    if not proxy_str.startswith(('http://', 'socks5://')):
        proxy_url = f'http://{proxy_str}'
    else:
        proxy_url = proxy_str
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://web.telegram.org', proxy=proxy_url, timeout=5) as resp:
                return resp.status == 200
    except:
        return False

async def get_working_proxy_for_account(account_name: str, proxy_pool: List[str], used_proxies: Dict[str, str]) -> Optional[str]:
    available = [p for p in proxy_pool if p not in used_proxies.values()]
    random.shuffle(available)
    for proxy in available:
        if await check_proxy(proxy):
            used_proxies[account_name] = proxy
            return proxy
    for proxy in proxy_pool:
        if proxy in used_proxies.values():
            continue
        if await check_proxy(proxy):
            used_proxies[account_name] = proxy
            return proxy
    attack_logger.error(f"Нет рабочих прокси для аккаунта {account_name}")
    return None

failed_accounts = {}
failed_accounts_limit = 2
account_blacklist = set()

def mark_account_failed(account_name: str, reason: str):
    global failed_accounts
    attack_logger.warning(f"Аккаунт {account_name} получил ошибку: {reason}")
    if account_name not in failed_accounts:
        failed_accounts[account_name] = 0
    failed_accounts[account_name] += 1
    account_blacklist.add(account_name)
    if len([a for a, c in failed_accounts.items() if c >= 1]) >= failed_accounts_limit:
        attack_logger.critical(f"Ошибки на {failed_accounts_limit} аккаунтах. Останавливаем Telethon-репортер.")
        raise Exception("STOP_ATTACK_DUE_TO_ACCOUNT_FAILURES")

def is_account_banned(account_name: str) -> bool:
    return account_name in account_blacklist

def load_all_sessions():
    from pathlib import Path
    sess_dir = Path(SESSIONS_DIR)
    if not sess_dir.exists():
        return []
    return list(sess_dir.glob("*.session"))