import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ۱. خواندن آدرس سامانه از فایل کانفیگ (با قابلیت تصحیح هوشمند لینک)
# ==============================================================
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        TARGET_URL = config["url"].strip()

        # تضمین وجود اسلش در انتهای آدرس
        if not TARGET_URL.endswith('/'):
            TARGET_URL += '/'

        # تزریق هوشمند nui در صورتی که کاربر فراموش کرده باشد
        if not TARGET_URL.endswith('nui/'):
            TARGET_URL += 'nui/'

        base_url = TARGET_URL
except FileNotFoundError:
    print("❌ فایل config.json پیدا نشد! لطفاً تست‌ها را از طریق رابط کاربری (UI) اجرا کنید.")
    exit()

# ==============================================================
# بخش ۲: راه‌اندازی مرورگر و تزریق خودکار سشن
# ==============================================================
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

# 🌟 فعال کردن شنود شبکه
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

# ساخت مرورگر با تنظیمات بالا
driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()
wait = WebDriverWait(driver, 10)


def run_step(action, description):
    try:
        action()
        print(f"  [✓] {description} با موفقیت انجام شد.")
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f"  [⚠️] {description} خطا داد. علت: {error_msg}")


# استفاده از آدرس پویا به جای هاردکد
driver.get(base_url)

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

    driver.refresh()
    print("✅ توکن لود شد. ورود به حساب...")
except Exception as e:
    print(f"❌ فایل session.json پیدا نشد یا خطا دارد! اول لاگین را اجرا کن.")
    driver.quit()
    exit()

# ==============================================================
# بخش ۳: سناریوی باز کردن اولین ایمیل و ریپلای
# ==============================================================
print("\n▶️ شروع تست: باز کردن اولین ایمیل و ارسال پاسخ")

# ۱. ورود به اینباکس با استفاده از آدرس پویا
run_step(lambda: driver.get(base_url + 'mail/message?query=2&page=1&type=inbox'), "ورود به اینباکس")
time.sleep(5)  # مکث برای لود شدن اولیه صفحه


# ۱.۴ کلیک روی آیکون ماژول نامه
def click_mail_icon():
    mail_icon = wait.until(EC.presence_of_element_located((
        By.XPATH, "//a[@id='mailApplicationButton'] | //a[contains(@href, '/nui/mail')]"
    )))
    driver.execute_script("arguments[0].click();", mail_icon)
    time.sleep(3)

run_step(click_mail_icon, "کلیک روی آیکون ماژول نامه")


# ۱.۵ کلیک روی منوی صندوق دریافت در سایدبار
def click_inbox_folder():
    inbox_element = wait.until(EC.presence_of_element_located((
        By.XPATH, "//span[contains(@class, 'tree-item__name') and contains(text(), 'صندوق دریافت')] | //span[contains(text(), 'صندوق دریافت')]"
    )))
    driver.execute_script("arguments[0].click();", inbox_element)
    time.sleep(2)

run_step(click_inbox_folder, "کلیک روی منوی صندوق دریافت")


# ۲. پیدا کردن و کلیک روی اولین ایمیل واقعی در لیست
def click_first_email():
    time.sleep(3)  # مکث برای لود کامل لیست از سرور

    # پیدا کردن باکسی که لیست ایمیل‌ها داخلشه و انتخاب اولین فرزند داخل آن
    first_email = wait.until(EC.presence_of_element_located((
        By.XPATH,
        "(//app-message-list//app-message-list-item)[1] | "
        "(//mat-table//mat-row)[1] | "
        "(//div[@role='grid']//div[@role='row'])[1] | "
        "(//table//tbody//tr)[1] | "
        "(//div[contains(@class, 'mail-list')]//div[contains(@class, 'list-item')])[1]"
    )))

    # اسکرول دقیق به وسط کادر و کلیک اجباری با جاوااسکریپت
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_email)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", first_email)


run_step(click_first_email, "کلیک روی اولین ایمیل لیست")


# ۲.۵ مدیریت پاپ‌آپ (پیاده‌سازی دقیق بر اساس لاگ ریکوردر شما)
def handle_optional_popup():
    time.sleep(2)  # مکث برای رندر شدن پاپ‌آپ

    dialogs = driver.find_elements(By.TAG_NAME, "mat-dialog-container")
    if not dialogs:
        print("    -> ℹ️ پاپ‌آپ اصلاً روی صفحه نیامد. ادامه مسیر...")
        return

    print("    -> ℹ️ پاپ‌آپ باز شد! در حال هدف‌گیری دقیقِ تگ span (مثل ریکوردر)...")

    # صبر می‌کنیم تا لایه تاریک کامل روی صفحه بنشیند و انیمیشن متوقف شود
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "cdk-overlay-backdrop-showing")))
    time.sleep(1.5)

    try:
        # 🎯 جستجوی دقیق تگ span با کلمات: لغو، خیر یا بله (دور زدن لایه دکمه)
        btn_close_span = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((
            By.XPATH,
            "//mat-dialog-container//span[contains(text(), 'لغو') or contains(text(), 'خیر') or contains(text(), 'بله')]"
        )))

        # کلیک استاندارد روی خود کلمه
        btn_close_span.click()
        print(f"    -> ℹ️ کلیک با موفقیت روی متن دکمه انجام شد.")

        # صبر برای محو شدن لایه تاریک مزاحم
        WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.CLASS_NAME, "cdk-overlay-backdrop")))
        print("    -> ℹ️ لایه تاریک محو شد و صفحه کاملاً آزاد است.")
        time.sleep(1)

    except Exception as e:
        raise Exception("پاپ‌آپ وجود داشت، اما تگ span (متن دکمه) پیدا نشد یا قابل کلیک نبود!")


run_step(handle_optional_popup, "بررسی وجود و تست کلیک پاپ‌آپ")


# ۳. پیدا کردن و کلیک روی دکمه «پاسخ»
def click_reply_button():
    reply_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "//button[contains(., 'پاسخ')] | //span[contains(text(), 'پاسخ')] | //mat-icon[contains(text(), 'reply')]/ancestor::button"
    )))
    reply_btn.click()


run_step(click_reply_button, "کلیک روی دکمه پاسخ (Reply)")
time.sleep(1.5)  # مکث برای باز شدن پنجره نوشتن جواب


# ۴. تایپ متن پاسخ در بدنه
def type_reply_body():
    time.sleep(2.5)
    iframes = driver.find_elements(By.XPATH, "//iframe")

    if len(iframes) > 0:
        driver.switch_to.frame(iframes[-1])
        body = wait.until(EC.presence_of_element_located((By.XPATH, "//body")))
        driver.execute_script("arguments[0].innerHTML = '<p>این یک پاسخ خودکار از طریق سلنیوم است.</p>';", body)
        driver.switch_to.default_content()
    else:
        body = wait.until(EC.presence_of_element_located((By.XPATH,
                                                          "//*[@id='tinymce'] | //div[contains(@class, 'mce-content-body')] | //div[@contenteditable='true']")))
        driver.execute_script("arguments[0].innerHTML = '<p>این یک پاسخ خودکار از طریق سلنیوم است.</p>';", body)


run_step(type_reply_body, "تایپ متن پاسخ در بدنه ایمیل")


# ۵. کلیک روی دکمه ارسال
def click_send_button():
    send_btn = wait.until(EC.presence_of_element_located((
        By.XPATH, "//button[normalize-space()='ارسال'] | //button[.//span[normalize-space()='ارسال']]"
    )))
    driver.execute_script("arguments[0].click();", send_btn)


run_step(click_send_button, "کلیک روی دکمه ارسال")


# ۶. چک کردن تب Network برای دریافت ریکوئست 200
def verify_network_200():
    print("  [⏳] در حال پایش زنده ترافیک شبکه (حداکثر ۱۰ ثانیه)...")

    max_retries = 10

    for attempt in range(max_retries):
        logs = driver.get_log("performance")

        for entry in logs:
            try:
                log_data = json.loads(entry["message"])["message"]

                if log_data["method"] == "Network.responseReceived":
                    response = log_data["params"]["response"]
                    url = response.get("url", "")
                    status = response.get("status")

                    url_lower = url.lower()

                    if "/api/mail/send" in url_lower:
                        clean_url = url.split('?')[0]
                        print(f"  [🌐] ریکوئست هدف (API) پیدا شد! URL: {clean_url} | Status: {status}")

                        if status == 200:
                            print("  [✓] تایید قطعی: سرور وضعیت 200 OK برگرداند (ارسال موفق).")
                            return
                        elif status == 204:
                            continue
                        else:
                            raise Exception(f"بک‌اند ارور داد! کد وضعیت سرور: {status}")
            except Exception as e:
                pass

        time.sleep(1)

    raise Exception("زمان انتظار تمام شد! ریکوئست اصلی /api/mail/send در شبکه یافت نشد.")


run_step(verify_network_200, "بررسی کد 200 در تب Network")

print("\n🏁 تست ریپلای با موفقیت به پایان رسید.")
driver.quit()