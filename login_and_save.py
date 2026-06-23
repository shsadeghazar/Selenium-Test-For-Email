import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ۱. خواندن اطلاعات از فایل کانفیگ (که توسط UI ساخته می‌شود)
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        TARGET_URL = config["url"]
        USERNAME = config["username"]
        PASSWORD = config["password"]
except FileNotFoundError:
    print("❌ فایل config.json پیدا نشد! لطفاً تست‌ها را از طریق رابط کاربری (UI) اجرا کنید.")
    exit()

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

try:
    print("در حال لاگین و دریافت توکن...")

    # ۲. استفاده از آدرس پویا (جلوگیری از خطای تایپی اسلش در انتهای لینک)
    base_url = TARGET_URL if TARGET_URL.endswith('/') else TARGET_URL + '/'
    driver.get(base_url + 'auth/login')

    # ۳. تزریق یوزرنیم و پسورد پویا
    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'کاربری') or @type='text']"))).send_keys(
        USERNAME)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='password']"))).send_keys(PASSWORD)

    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[@id='loginbtn'] | //button[contains(., 'ورود')]"))).click()

    time.sleep(5)  # مکث برای دریافت کامل توکن‌ها

    # ذخیره سشن
    session_data = {
        "cookies": driver.get_cookies(),
        "local_storage": driver.execute_script(
            "var ls = window.localStorage, items = {}; "
            "for (var i = 0, k; i < ls.length; ++i) { k = ls.key(i); items[k] = ls.getItem(k); } "
            "return items; "
        )
    }

    with open("session.json", "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=4)

    print("✅ لاگین موفق! توکن با موفقیت از سرور هدف دریافت و در session.json ذخیره شد.")

except Exception as e:
    print(f"❌ خطایی در فرآیند لاگین رخ داد: {str(e)}")

finally:
    driver.quit()
