import os

API_ID = 
API_HASH = "-"
HASH_PASSWORD = "preparat2025"


REQUIRED_MODULES = [
    "asyncio", "aiohttp", "random", "string", "time",
    "termcolor", "fake_useragent", "telethon", "numpy",
    "undetected_chromedriver", "selenium", "selenium_stealth"
]

CODE_ATTACK_COUNT = 1       # количество запросов кода 
CODE_DELAY_MEAN = 14            # средняя задержка между запросами (сек)
CODE_DELAY_STD = 4

SESSIONS_DIR = "sessions"       
REPORTS_PER_SESSION = 1         # скок жб отправит каждый ак
REPORT_DELAY_TELEGRAM = (60, 120)  # задержка между жб с 1 ака

REPORT_URL = "https://telegram.org/support"
#WEB_REPORT_DELAY_MEAN = 60     # 15 мин
#WEB_REPORT_DELAY_STD = 30     # 5 мин
CAPTCHA_API_KEY = ""            # Если есть)
PROXY_FILE = "proxy_list.txt"