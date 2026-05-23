import asyncio
import random
from pathlib import Path
from telethon import TelegramClient, functions, types
from telethon.errors import FloodWaitError, PhoneNumberBannedError, AuthKeyError
from telethon.tl.types import (
    InputReportReasonSpam,
    InputReportReasonViolence,
    InputReportReasonChildAbuse,
    InputReportReasonFake,
    InputReportReasonIllegalDrugs,
    InputReportReasonPornography
)
from termcolor import colored
from config import API_ID, API_HASH, SESSIONS_DIR, REPORTS_PER_SESSION, REPORT_DELAY_TELEGRAM
from report_data import make_report_text
from protector import mark_account_failed, is_account_banned, get_working_proxy_for_account, check_proxy
from logger_utils import attack_logger
from code_attacker import load_proxy_list


proxy_list = load_proxy_list()
used_proxies = {}

REPORT_REASONS = [
    types.InputReportReasonSpam(),
    types.InputReportReasonViolence(),
    types.InputReportReasonChildAbuse(),
    types.InputReportReasonFake(),
    types.InputReportReasonIllegalDrugs(),
    types.InputReportReasonPornography()
]

async def load_sessions():
    session_dir = Path(SESSIONS_DIR)
    if not session_dir.exists():
        print(colored(f"[-] Папка {SESSIONS_DIR} не найдена", "red"))
        return []
    sessions = list(session_dir.glob("*.session"))
    if not sessions:
        print(colored(f"[-] В {SESSIONS_DIR} нет .session файлов", "red"))
    return sessions

async def send_report_from_session(session_path, target_id, target_phone):
    client = None
    account_name = session_path.stem
    if is_account_banned(account_name):
        attack_logger.info(f"Ак {account_name} пропущен (ранее оказался в чс)")
        return False
    
    proxy = None
    if proxy_list:
        proxy = await get_working_proxy_for_account(account_name, proxy_list, used_proxies)
        if proxy:
            proxy_tuple = ('socks5', proxy.split(':')[0], int(proxy.split(':')[1]), None, None)
        else:
            proxy_tuple = None
    else:
        proxy_tuple = None
    
    try:
        client = TelegramClient(str(session_path), API_ID, API_HASH, proxy=proxy_tuple)
        await client.connect()
        if not await client.is_user_authorized():
            attack_logger.warning(f"Ак {account_name} не авторизован")
            mark_account_failed(account_name, "not_authorized")
            return False
        
        me = await client.get_me()
        reason = random.choice(REPORT_REASONS)
        text = make_report_text(target_id, target_phone)
        
       
        await client(functions.messages.ReportRequest(
            peer=target_id,
            reason=[reason],   
            message=text
        ))

        attack_logger.info(f"Жб отправлена с {account_name} (@{me.username}) на цель {target_id}")
        print(colored(f"[+] Жб отправлена с {account_name}", "green"))
        return True
        
    except FloodWaitError as e:
        attack_logger.warning(f"Ак {account_name} получил flood wait {e.seconds} сек")
        mark_account_failed(account_name, f"flood_wait_{e.seconds}")
        return False
    except (PhoneNumberBannedError, AuthKeyError) as e:
        attack_logger.error(f"Ак {account_name} заблокирован....( : {e}")
        mark_account_failed(account_name, "banned")
        return False
    except Exception as e:
        attack_logger.error(f"Ошибка на акке {account_name}: {e}")
        mark_account_failed(account_name, str(e)[:50])
        return False
    finally:
        if client:
            await client.disconnect()

async def mass_telethon_reports(target_id, target_phone, reports_per_session=REPORTS_PER_SESSION):
    sessions = await load_sessions()
    if not sessions:
        print(colored("[-] Нет сессий. Telethon-репортер скипнут.", "red"))
        attack_logger.warning("Нет сессий для Telethon-репортера")
        return 0
    
    global used_proxies
    used_proxies = {}
    total_success = 0
    try:
        for session_path in sessions:
            account_name = session_path.stem
            if is_account_banned(account_name):
                continue
            for i in range(reports_per_session):
                print(colored(f"[*] Жб {i+1}/{reports_per_session} с {account_name}", "cyan"))
                ok = await send_report_from_session(session_path, target_id, target_phone)
                if ok:
                    total_success += 1
                await asyncio.sleep(random.uniform(*REPORT_DELAY_TELEGRAM))
    except Exception as e:
        if str(e) == "STOP_ATTACK_DUE_TO_ACCOUNT_FAILURES":
            attack_logger.critical("Telethon-репортер стопнут из-за ошибок на акках")
            print(colored("\n[!] Два акка подряд получили ошибки – Telethon-атака прервана...", "red"))
        else:
            raise
    attack_logger.info(f"Telethon-жб успешно: {total_success}")
    print(colored(f"[+] Telethon-жб успешно: {total_success}", "green"))
    return total_success