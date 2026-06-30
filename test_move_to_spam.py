import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================
# بخش ۱: خواندن کانفیگ، تنظیمات مرورگر و تزریق سشن
# ==============================================================
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    TARGET_URL = config["url"].strip()
    if not TARGET_URL.endswith('/'): TARGET_URL += '/'
    if not TARGET_URL.endswith('nui/'): TARGET_URL += 'nui/'
    base_url = TARGET_URL
except FileNotFoundError:
    print("❌ فایل config.json پیدا نشد! لطفاً تست‌ها را از طریق رابط کاربری اجرا کنید.")
    exit()

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--start-maximized")
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)


def run_step(action, description):
    try:
        result = action()
        if result != "SKIP_LOG" and not description.startswith("->"):
            print(f" [✓] {description} با موفقیت انجام شد.")
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f" [⚠️] {description} خطا داد. علت: {error_msg}")


# باز کردن صفحه خنثی برای جلوگیری از ریدایرکت لاگین پیش از تزریق سشن
driver.get(base_url + "robots.txt")

try:
    with open("session.json", "r", encoding="utf-8") as f:
        session_data = json.load(f)
    for cookie in session_data.get("cookies", []):
        driver.add_cookie(cookie)
    for key, value in session_data.get("local_storage", {}).items():
        safe_value = json.dumps(value) if not isinstance(value, str) else f"'{value}'"
        driver.execute_script(f"window.localStorage.setItem('{key}', {safe_value});")
    for key, value in session_data.get("session_storage", {}).items():
        safe_value = json.dumps(value) if not isinstance(value, str) else f"'{value}'"
        driver.execute_script(f"window.sessionStorage.setItem('{key}', {safe_value});")
    print("✅ توکن لود شد. ورود به حساب...")
except Exception as e:
    print(f"❌ فایل session.json پیدا نشد یا خطا دارد!")
    driver.quit()
    exit()

# ==============================================================
# بخش ۲: سناریوی اصلی (کلیک و پایش ریکوئست انتقال به هرزنامه)
# ==============================================================
try:
    print("\n▶️ شروع تست: انتقال اولین ایمیل به صندوق هرزنامه (Spam)")


    # لود کردن آدرس اصلی پس از تزریق امن سشن
    def open_initial_page():
        driver.get(base_url)
        time.sleep(2)


    run_step(open_initial_page, "لود صفحه اصلی سامانه")


    # کلیک روی آیکون ماژول نامه (رایانامه)
    def click_mail_icon():
        mail_icon = wait.until(EC.presence_of_element_located((
            By.XPATH, "//a[@id='mailApplicationButton'] | //a[contains(@href, '/nui/mail')]"
        )))
        driver.execute_script("arguments[0].click();", mail_icon)
        time.sleep(3)


    run_step(click_mail_icon, "کلیک روی آیکون ماژول نامه")


    # کلیک روی منوی صندوق دریافت در سایدبار
    def click_inbox_folder():
        inbox_element = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//span[contains(@class, 'tree-item__name') and contains(text(), 'صندوق دریافت')] | //span[contains(text(), 'صندوق دریافت')]"
        )))
        driver.execute_script("arguments[0].click();", inbox_element)
        time.sleep(2)


    run_step(click_inbox_folder, "کلیک روی منوی صندوق دریافت")


    # هدایت مستقیم به کوئری اینباکس جهت اطمینان از ساختار لیست اول ایمیل‌ها
    def open_inbox():
        driver.get(base_url + 'mail/message?query=2&page=1&type=inbox')
        time.sleep(4)


    run_step(open_inbox, "ورود به اینباکس")


    # کلیک روی منوی 'more_vert' ایمیل اول
    def click_more_vert():
        menu_btn = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "(//tbody//tr[1]//app-table-action-single//button)[1] | (//button[.//span[contains(@class, 'mat-focus-indicator')]])[last()]"
        )))
        driver.execute_script("arguments[0].click();", menu_btn)
        time.sleep(1.5)


    run_step(click_more_vert, "کلیک روی منوی 'more_vert' ایمیل اول")


    # کلیک روی گزینه انتقال به هرزنامه
    def click_move_to_spam():
        spam_btn = wait.until(EC.presence_of_element_located((
            By.XPATH, "//span[contains(text(),'انتقال به هرزنامه')] | //span[normalize-space()='انتقال به هرزنامه']"
        )))
        driver.execute_script("arguments[0].click();", spam_btn)


    run_step(click_move_to_spam, "کلیک روی دکمه 'انتقال به هرزنامه'")


    # اعتبارسنجی شبکه برای شکار ریکوئست spam=true با وضعیت 200
    def verify_spam_network_request(timeout=15):
        print(" [⏳] در حال بررسی ریکوئست انتقال به هرزنامه در شبکه...")
        for _ in range(timeout):
            logs = driver.get_log("performance")
            for entry in logs:
                try:
                    log_data = json.loads(entry["message"])["message"]
                    if log_data["method"] == "Network.responseReceived":
                        response = log_data["params"]["response"]
                        url = response.get("url", "")
                        status = response.get("status")

                        if "api/mail/spam?spam=true" in url.lower():
                            clean_url = url.split('?')[1] if '?' in url else url
                            print(f" [🌐] شکار شد! پارامتر: {clean_url} | Status: {status}")
                            if status == 200:
                                return True
                            else:
                                raise Exception(f"بک‌اند ارور داد! وضعیت: {status}")
                except:
                    pass
            time.sleep(1)
        raise Exception("زمان تمام شد! ریکوئست انتقال به هرزنامه پیدا نشد.")


    run_step(verify_spam_network_request, "بررسی ترافیک شبکه (انتظار برای 200 در حالت spam=true)")

    print("\n🏁 تست انتقال ایمیل به هرزنامه با موفقیت به پایان رسید.")

finally:
    driver.quit()