import time
import json
import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ۱. خواندن اطلاعات از فایل کانفیگ (که توسط UI ساخته می‌شود)
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    TARGET_URL = config["url"].strip()
    USERNAME = config["username"].strip()
    PASSWORD = config["password"].strip()
except FileNotFoundError:
    print("❌ فایل config.json پیدا نشد! لطفاً تست‌ها را از طریق رابط کاربری (UI) اجرا کنید.")
    exit()

# تنظیم آدرس پایه پویا بدون هاردکد کردن دامنه
if not TARGET_URL.endswith('/'):
    TARGET_URL += '/'
base_url = TARGET_URL

# تنظیمات مرورگر
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)

def run_step(action, description):
    try:
        result = action()
        if result != "SKIP_LOG" and not str(description).startswith("->"):
            print(f" [✓] {description} با موفقیت انجام شد.")
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f" [⚠️] {description} خطا داد. علت: {error_msg}")
        raise e

try:
    print("\n▶️ شروع فرآیند لاگین و دریافت سشن جدید...")

    # باز کردن صفحه لاگین سامانه
    def open_login_page():
        driver.get(base_url)
    run_step(open_login_page, "باز کردن صفحه ورود سامانه")

    # وارد کردن نام کاربری
    def enter_username():
        user_input = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@name='username'] | //input[@type='text'] | //input[contains(@placeholder, 'کاربری')]"
        )))
        user_input.clear()
        user_input.send_keys(USERNAME)
    run_step(enter_username, "وارد کردن نام کاربری")

    # وارد کردن رمز عبور
    def enter_password():
        pass_input = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@name='password'] | //input[@type='password']"
        )))
        pass_input.clear()
        pass_input.send_keys(PASSWORD)
    run_step(enter_password, "وارد کردن رمز عبور")

    # کلیک روی دکمه ورود
    def click_login():
        login_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[@type='submit'] | //button[contains(., 'ورود')] | //span[contains(text(), 'ورود')]/ancestor::button"
        )))
        login_btn.click()
    run_step(click_login, "کلیک روی دکمه ورود")

    # انتظار برای ورود کامل به برنامه.
    # در ورود قدیمی مسیر نهایی معمولاً /nui/ است؛ در CAS ابتدا به دامنه
    # accounts منتقل می‌شویم و سپس به دامنه خود سامانه برمی‌گردیم.
    def wait_for_dashboard():
        target_host = (urlparse(base_url).hostname or "").lower()

        def login_is_complete(current_driver):
            current_host = (urlparse(current_driver.current_url).hostname or "").lower()
            if current_host != target_host:
                return False

            # تا وقتی فیلد رمز قابل مشاهده است، هنوز روی فرم ورود هستیم.
            visible_passwords = [
                element for element in current_driver.find_elements(By.XPATH, "//input[@type='password']")
                if element.is_displayed()
            ]
            if visible_passwords:
                return False

            return current_driver.execute_script("return document.readyState") == "complete"

        WebDriverWait(driver, 60).until(login_is_complete)
        # مکث کوتاهی جهت تثبیت ذخیره توکن‌ها در sessionStorage و Cookie
        time.sleep(2)
    run_step(wait_for_dashboard, "انتظار برای ورود به داشبورد و دریافت کامل توکن‌ها")

    # دریافت اطلاعات سشن
    # get_cookies در صفحه نهایی فقط کوکی‌های قابل استفاده روی دامنه خود
    # سامانه را می‌دهد؛ بنابراین کوکی مخصوص accounts وارد session.json
    # نمی‌شود ولی کوکی مشترک CAS مثل .iran.ir حفظ می‌شود.
    target_host = (urlparse(base_url).hostname or "").lower()
    cookies = []
    for cookie in driver.get_cookies():
        cookie_domain = str(cookie.get("domain", "")).lstrip(".").lower()
        if target_host == cookie_domain or target_host.endswith("." + cookie_domain):
            cookies.append(cookie)
    local_storage = driver.execute_script("return window.localStorage;")
    session_storage = driver.execute_script("return window.sessionStorage;")

    # در سامانه قدیمی توکن در sessionStorage و در CAS در localStorage است.
    csrf_token = (
        session_storage.get("ls.csrfToken", None)
        or local_storage.get("ls.csrfToken", None)
    )
    if csrf_token:
        print(f" [ℹ️] توکن CSRF با موفقیت استخراج شد: {csrf_token[:20]}...")
    else:
        print(" [⚠️] هشدار: کلید ls.csrfToken در sessionStorage پیدا نشد، اما کل سشن ذخیره خواهد شد.")

    session_data = {
        "app_base_url": (
            f"{urlparse(driver.current_url).scheme}://{urlparse(driver.current_url).netloc}"
            + (
                "/nui/"
                if urlparse(driver.current_url).path == "/nui"
                or urlparse(driver.current_url).path.startswith("/nui/")
                else "/"
            )
        ),
        "cookies": cookies,
        "local_storage": local_storage,
        "session_storage": session_storage
    }

    # ذخیره اطلاعات کامل سشن در session.json
    with open("session.json", "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=4)

    print(" [✓] اطلاعات سشن و CSRF Token جدید با موفقیت در session.json ذخیره شد.")

except Exception as e:
    print(f"❌ خطایی در فرآیند لاگین رخ داد: {str(e)}")
finally:
    driver.quit()
