import asyncio
import random
import string
import time
import os
import tempfile
import shutil
import numpy as np
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from termcolor import colored
from config import REPORT_URL, WEB_REPORT_DELAY_MEAN, WEB_REPORT_DELAY_STD, CAPTCHA_API_KEY
from report_data import make_report_text

# ---------- Загрузка прокси ----------
def load_proxies():
    if os.path.exists("proxy_list.txt"):
        with open("proxy_list.txt", "r") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

PROXY_LIST = load_proxies()
ua = UserAgent()

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Chrome/123.0.0.0 Safari/605.1.15",
]
SCREEN_RESOLUTIONS = [(1920,1080), (1366,768), (1536,864)]

def human_typing(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.05, 0.2))

def human_mouse_movement(driver, element):
    ActionChains(driver).move_to_element(element).perform()
    time.sleep(random.uniform(0.1, 0.3))

def random_scroll(driver):
    h = driver.execute_script("return document.body.scrollHeight")
    target = random.randint(100, max(200, h-100))
    driver.execute_script(f"window.scrollTo({{top: {target}, behavior: 'smooth'}});")
    time.sleep(random.uniform(0.5, 1.2))

def create_driver(proxy=None):
    options = uc.ChromeOptions()
    w, h = random.choice(SCREEN_RESOLUTIONS)
    options.add_argument(f"--window-size={w},{h}")
    options.add_argument(f'--user-agent={random.choice(UA_LIST)}')
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    # Временный профиль
    profile_dir = tempfile.mkdtemp(prefix="chrome_")
    options.add_argument(f"--user-data-dir={profile_dir}")
    
    # Указываем вашу версию Chrome, чтобы избежать конфликта
    # Если версия изменится (проверьте через google-chrome --version), замените число
    version_main = 144   # ← поставьте вашу версию
    driver = uc.Chrome(options=options, version_main=version_main, use_subprocess=True)
    return driver, profile_dir

def manual_captcha_input():
    print("\n" + "="*50)
    print("⚠️ Капча не распознана автоматически.")
    ans = input("Введите текст капчи вручную (или Enter чтобы пропустить): ").strip()
    return ans if ans else None

async def send_web_report(target_uid, target_phone, proxy=None):
    driver = None
    profile = None
    try:
        driver, profile = create_driver(proxy)
        driver.set_page_load_timeout(45)
        driver.get(REPORT_URL)
        time.sleep(random.uniform(3, 6))
        random_scroll(driver)
        wait = WebDriverWait(driver, 30)
        # Выбор темы
        subject_dropdown = wait.until(EC.element_to_be_clickable((By.NAME, "subject")))
        human_mouse_movement(driver, subject_dropdown)
        subject_dropdown.click()
        time.sleep(0.5)
        driver.find_element(By.XPATH, "//option[contains(text(),'Account compromised')]").click()
        time.sleep(1)
        # Email
        email = f"{''.join(random.choices(string.ascii_lowercase, k=10))}@gmail.com"
        email_field = driver.find_element(By.NAME, "email")
        human_typing(email_field, email)
        # Текст жалобы
        report_text = make_report_text(target_uid, target_phone)
        msg_field = driver.find_element(By.NAME, "message")
        human_typing(msg_field, report_text)
        time.sleep(2)
        # Капча
        img = driver.find_elements(By.CSS_SELECTOR, "img[alt='captcha']")
        if img:
            if CAPTCHA_API_KEY:
                print(colored("[*] Обнаружена капча, требуется ручной ввод", "yellow"))
                captcha_text = manual_captcha_input()
                if captcha_text:
                    captcha_field = driver.find_element(By.NAME, "captcha")
                    human_typing(captcha_field, captcha_text)
                else:
                    return False
            else:
                captcha_text = manual_captcha_input()
                if not captcha_text:
                    return False
                captcha_field = driver.find_element(By.NAME, "captcha")
                human_typing(captcha_field, captcha_text)
        # Отправка
        submit = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].scrollIntoView(true);", submit)
        time.sleep(1)
        human_mouse_movement(driver, submit)
        time.sleep(1)
        submit.click()
        time.sleep(6)
        if "спасибо" in driver.page_source.lower() or "thank you" in driver.page_source.lower():
            print(colored("[+] Веб-жалоба отправлена успешно", "green"))
            return True
        else:
            print(colored("[-] Ошибка: подтверждение не найдено", "red"))
            return False
    except Exception as e:
        print(colored(f"[-] Ошибка веб-жалобы: {e}", "red"))
        return False
    finally:
        if driver:
            driver.quit()
        if profile and os.path.exists(profile):
            shutil.rmtree(profile, ignore_errors=True)

async def mass_web_reports_free(target_id, target_phone, count):
    print(colored(f"[*] Запуск веб-жалоб (браузер). Цель: {target_id}, кол-во: {count}", "yellow"))
    success = 0
    for i in range(1, count+1):
        proxy = random.choice(PROXY_LIST) if PROXY_LIST else None
        delay = max(30, np.random.normal(WEB_REPORT_DELAY_MEAN, WEB_REPORT_DELAY_STD))
        print(colored(f"   Жалоба {i}/{count}. Пауза {delay/60:.1f} мин. Прокси: {proxy or 'нет'}", "cyan"))
        await asyncio.sleep(delay)
        ok = await send_web_report(target_id, target_phone, proxy)
        if ok:
            success += 1
        await asyncio.sleep(random.uniform(5, 15))
    print(colored(f"[+] Веб-жалоб отправлено успешно: {success}/{count}", "green"))
    return success