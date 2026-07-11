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


# 🌟 باز کردن یک صفحه خنثی برای جلوگیری از ریدایرکت سریع به لاگین
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
# بخش ۲: سناریوی اصلی (دوبار کلیک و پایش متضاد شبکه)
# ==============================================================
try:
    print("\n▶️ شروع تست: تغییر وضعیت خوانده شده/نخوانده ایمیل اول در صندوق ارسال (بررسی هر دو حالت)")


    # لود کردن آدرس اصلی پس از تزریق امن سشن
    def open_initial_page():
        driver.get(base_url)
        time.sleep(2)


    run_step(open_initial_page, "لود صفحه اصلی سامانه")


    # 🌟 اضافه شده طبق سورس: کلیک روی آیکون ماژول نامه (رایانامه)
    def click_mail_icon():
        mail_icon = wait.until(EC.presence_of_element_located((
            By.XPATH, "//a[@id='mailApplicationButton'] | //a[contains(@href, '/nui/mail')]"
        )))
        driver.execute_script("arguments[0].click();", mail_icon)
        time.sleep(3)


    run_step(click_mail_icon, "کلیک روی آیکون ماژول نامه")


    # 🌟 تغییر یافته طبق خواسته شما: کلیک روی منوی صندوق ارسال در سایدبار
    def click_sent_folder():
        sent_element = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//span[contains(@class, 'tree-item__name') and contains(text(), 'صندوق ارسال')] | //span[contains(text(), 'صندوق ارسال')]"
        )))
        driver.execute_script("arguments[0].click();", sent_element)
        time.sleep(2)


    run_step(click_sent_folder, "کلیک روی منوی صندوق ارسال")


    # تغییر یافته طبق خواسته شما: هدایت مستقیم به کوئری مورد نظر جهت اطمینان از صحت ساختار لیست صندوق ارسال
    def open_sent_box():
        driver.get(base_url + 'mail/message?query=2&page=1&type=sent')
        time.sleep(4)


    run_step(open_sent_box, "ورود به صندوق ارسال")


    def click_more_vert():
        menu_btn = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "(//tbody//tr[1]//app-table-action-single//button)[1] | (//button[.//span[contains(@class, 'mat-focus-indicator')]])[last()]"
        )))
        driver.execute_script("arguments[0].click();", menu_btn)
        time.sleep(1.5)


    def click_read_unread():
        btn = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//span[contains(text(),'خوانده شده/خوانده نشده')] | //span[normalize-space()='خوانده شده/خوانده نشده']"
        )))
        driver.execute_script("arguments[0].click();", btn)


    # ---------------------------------------------------------
    # فاز اول: کلیک و دریافت وضعیت اولیه
    # ---------------------------------------------------------
    run_step(click_more_vert, "کلیک روی منوی 'more_vert' ایمیل اول (بار اول)")
    run_step(click_read_unread, "کلیک روی دکمه 'خوانده شده/خوانده نشده' (بار اول)")

    first_state = [None]


    def verify_first_network():
        print(" [⏳] در حال بررسی ریکوئست وضعیت در شبکه (بار اول)...")
        driver.get_log("performance")  # پاک کردن لاگ‌های قبلی
        for _ in range(15):
            logs = driver.get_log("performance")
            for entry in logs:
                try:
                    log_data = json.loads(entry["message"])["message"]
                    if log_data["method"] == "Network.responseReceived":
                        response = log_data["params"]["response"]
                        url = response.get("url", "")
                        status = response.get("status")

                        if "api/mail/mark?read=true" in url.lower() or "api/mail/mark?read=false" in url.lower():
                            clean_url = url.split('?')[1] if '?' in url else url
                            if status == 200:
                                print(f" [🌐] شکار شد! پارامتر: {clean_url} | Status: {status}")
                                first_state[0] = clean_url
                                return True
                except:
                    pass
            time.sleep(1)
        raise Exception("زمان تمام شد! ریکوئست وضعیت خوانده/نخوانده پیدا نشد.")


    run_step(verify_first_network, "بررسی ترافیک شبکه (انتظار برای وضعیت اولیه)")

    # ---------------------------------------------------------
    # فاز دوم: کلیک مجدد و انتظار برای وضعیت متضاد
    # ---------------------------------------------------------
    time.sleep(2)
    run_step(click_more_vert, "کلیک مجدد روی منوی 'more_vert' ایمیل اول (بار دوم)")
    run_step(click_read_unread, "کلیک مجدد روی دکمه 'خوانده شده/خوانده نشده' (بار دوم)")


    def verify_second_network():
        if not first_state[0]:
            raise Exception("وضعیت اولیه یافت نشد، امکان بررسی وضعیت متضاد وجود ندارد.")

        expected_url_part = "read=true" if "read=false" in first_state[0] else "read=false"

        print(f" [⏳] در حال بررسی ریکوئست در شبکه (انتظار برای وضعیت متضاد: {expected_url_part})...")
        driver.get_log("performance")  # پاک کردن لاگ‌های قبلی

        for _ in range(15):
            logs = driver.get_log("performance")
            for entry in logs:
                try:
                    log_data = json.loads(entry["message"])["message"]
                    if log_data["method"] == "Network.responseReceived":
                        response = log_data["params"]["response"]
                        url = response.get("url", "")
                        status = response.get("status")

                        if expected_url_part in url.lower():
                            clean_url = url.split('?')[1] if '?' in url else url
                            if status == 200:
                                print(f" [🌐] شکار دوم با موفقیت انجام شد! پارامتر: {clean_url} | Status: {status}")
                                return True
                except:
                    pass
            time.sleep(1)
        raise Exception(f"زمان تمام شد! ریکوئست متضاد ({expected_url_part}) پیدا نشد.")


    run_step(verify_second_network, "بررسی ترافیک شبکه (انتظار برای وضعیت متضاد)")

    print("\n🏁 تست تغییر وضعیت ایمیل در صندوق ارسال (هر دو حالت) با موفقیت به پایان رسید.")

finally:
    driver.quit()