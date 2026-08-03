import json
import secrets
import string
import time
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# ==============================================================
# ۱. خواندن کانفیگ و آماده‌سازی آدرس سامانه
# ==============================================================
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    TARGET_URL = config["url"].strip()
    random_characters = string.ascii_letters + string.digits
    EVENT_SUBJECT = "".join(secrets.choice(random_characters) for _ in range(12))
    EVENT_NOTE = "".join(secrets.choice(random_characters) for _ in range(24))
    EVENT_CALENDAR = "تقویم پیش فرض"
    # فیلد «To» رابط کاربری در config.json با نام target_email ذخیره می‌شود.
    EVENT_INVITEE = config.get("target_email", "").strip()
    if not EVENT_INVITEE:
        raise ValueError("فیلد To (target_email) در config.json خالی است")

    if not TARGET_URL.endswith("/"):
        TARGET_URL += "/"
    if not TARGET_URL.endswith("nui/"):
        TARGET_URL += "nui/"

    base_url = TARGET_URL
except FileNotFoundError:
    print("❌ فایل config.json پیدا نشد! لطفاً تست‌ها را از طریق رابط کاربری (UI) اجرا کنید.")
    raise SystemExit(1)
except (KeyError, ValueError, json.JSONDecodeError) as e:
    print(f"❌ فایل config.json معتبر نیست: {e}")
    raise SystemExit(1)


# ==============================================================
# ۲. راه‌اندازی مرورگر و تزریق سشن
#    دقیقاً با الگوی سالم test_reply_with_signature.py
# ==============================================================
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--start-maximized")
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)
step_failures = []


def run_step(action, description):
    try:
        result = action()
        if result != "SKIP_LOG" and not description.startswith("->"):
            print(f"  [✓] {description} با موفقیت انجام شد.")
        return True
    except Exception as e:
        error_msg = str(e).split("\n")[0]
        step_failures.append((description, error_msg))
        print(f"  [⚠️] {description} خطا داد. علت: {error_msg} (تست ادامه می‌یابد...)")
        return False


driver.get(base_url + "robots.txt")

try:
    with open("session.json", "r", encoding="utf-8") as f:
        session_data = json.load(f)

    for cookie in session_data.get("cookies", []):
        driver.add_cookie(cookie)

    for key, value in session_data.get("local_storage", {}).items():
        driver.execute_script(
            "window.localStorage.setItem(arguments[0], arguments[1]);",
            key,
            value if isinstance(value, str) else json.dumps(value, ensure_ascii=False),
        )

    for key, value in session_data.get("session_storage", {}).items():
        driver.execute_script(
            "window.sessionStorage.setItem(arguments[0], arguments[1]);",
            key,
            value if isinstance(value, str) else json.dumps(value, ensure_ascii=False),
        )

    driver.get(base_url)
    print("✅ توکن لود شد. ورود به حساب...")
except Exception as e:
    print(f"❌ فایل session.json پیدا نشد یا خطا دارد! اول لاگین را اجرا کن. علت: {str(e).splitlines()[0]}")
    driver.quit()
    raise SystemExit(1)


# ==============================================================
# ۳. توابع کمکی سناریو
# ==============================================================
def wait_for_loading_to_finish():
    for selector in (".splash-screen", ".loading-shade", "mat-progress-spinner"):
        try:
            WebDriverWait(driver, 4).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
            )
        except Exception:
            pass


def safe_click(element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


def is_create_event_url(url):
    path = urlparse(url).path.rstrip("/").lower()
    return path.endswith("/api/cal") or path.endswith("/cal")


def verify_create_event_request(timeout=20):
    print("  [⏳] در حال پایش شبکه برای ساخت رویداد (حداکثر ۲۰ ثانیه)...")
    request_methods = {}
    end_time = time.time() + timeout

    while time.time() < end_time:
        for entry in driver.get_log("performance"):
            try:
                message = json.loads(entry["message"])["message"]
                method = message.get("method")
                params = message.get("params", {})

                if method == "Network.requestWillBeSent":
                    request = params.get("request", {})
                    request_methods[params.get("requestId")] = request.get("method", "")
                    continue

                if method != "Network.responseReceived":
                    continue

                response = params.get("response", {})
                request_id = params.get("requestId")
                url = response.get("url", "")
                status = int(response.get("status", 0))
                request_method = request_methods.get(request_id, "POST")

                if request_method.upper() != "POST" or not is_create_event_url(url):
                    continue

                clean_url = url.split("?", 1)[0]
                print(f"  [🌐] ریکوئست ساخت رویداد پیدا شد! URL: {clean_url} | Status: {status}")

                if status in (200, 201):
                    print("  [✓] تایید قطعی: رویداد با پاسخ موفق بک‌اند ساخته شد.")
                    return True

                raise Exception(f"بک‌اند هنگام ساخت رویداد خطا داد! کد وضعیت: {status}")
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue

        time.sleep(0.5)

    raise Exception("زمان انتظار تمام شد! ریکوئست POST ساخت رویداد (/api/cal یا /cal) در شبکه یافت نشد.")


# ==============================================================
# ۴. سناریوی اصلی: ساخت رویداد در تقویم
# ==============================================================
try:
    print("\n▶️ شروع تست: ساخت رویداد جدید در تقویم")

    def open_inbox():
        driver.get(base_url + "mail/message?query=2&page=1&type=inbox")
        wait_for_loading_to_finish()
        time.sleep(2)

    run_step(open_inbox, "ورود به اینباکس")

    def open_calendar_module():
        calendar_button = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//a[@id='calendarApplicationButton'] | "
                    "//a[contains(@href, '/nui/calendar')]",
                )
            )
        )
        safe_click(calendar_button)
        WebDriverWait(driver, 10).until(EC.url_contains("/calendar"))
        wait_for_loading_to_finish()
        time.sleep(2)

    run_step(open_calendar_module, "کلیک روی آیکون ماژول تقویم")

    def click_new_event():
        new_event_button = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//button[.//span[normalize-space()='رویداد جدید']] | "
                    "//button[contains(normalize-space(.), 'رویداد جدید')]",
                )
            )
        )
        safe_click(new_event_button)
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//app-event-form-modal"))
        )

    run_step(click_new_event, "کلیک روی دکمه رویداد جدید")

    def enter_subject():
        subject_input = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//app-event-form-modal//input[@name='name']")
            )
        )
        subject_input.click()
        subject_input.send_keys(Keys.CONTROL, "a")
        subject_input.send_keys(Keys.BACKSPACE)
        subject_input.send_keys(EVENT_SUBJECT)

    run_step(enter_subject, f"وارد کردن موضوع رویداد: {EVENT_SUBJECT}")

    def choose_calendar():
        calendar_select = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//app-event-form-modal//mat-select[@name='folderId']")
            )
        )
        safe_click(calendar_select)
        calendar_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f"//mat-option[.//span[normalize-space()={json.dumps(EVENT_CALENDAR, ensure_ascii=False)}] "
                    f"or normalize-space()={json.dumps(EVENT_CALENDAR, ensure_ascii=False)}]",
                )
            )
        )
        safe_click(calendar_option)

    run_step(choose_calendar, f"انتخاب تقویم: {EVENT_CALENDAR}")

    def enter_note():
        note_input = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//app-event-form-modal//textarea[@name='note']")
            )
        )
        note_input.click()
        note_input.send_keys(Keys.CONTROL, "a")
        note_input.send_keys(Keys.BACKSPACE)
        note_input.send_keys(EVENT_NOTE)

    run_step(enter_note, f"وارد کردن یادداشت رویداد: {EVENT_NOTE}")

    def open_contact_selector():
        contact_button = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//app-event-form-modal//button[.//app-font-icon[@name='person_add'] "
                    "or .//i[normalize-space()='person_add']]",
                )
            )
        )
        safe_click(contact_button)
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//app-contact-selector"))
        )

    run_step(open_contact_selector, "باز کردن پنجره انتخاب مخاطب برای مدعوین")

    def cancel_contact_selector():
        cancel_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//app-contact-selector//button[normalize-space()='لغو' "
                    "or .//span[normalize-space()='لغو']]",
                )
            )
        )
        safe_click(cancel_button)
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.XPATH, "//app-contact-selector"))
        )

    run_step(cancel_contact_selector, "لغو پنجره انتخاب مخاطب")

    def enter_invitee():
        if not EVENT_INVITEE:
            print("    -> ℹ️ ایمیل مدعو در config.json تنظیم نشده؛ این مرحله رد شد.")
            return "SKIP_LOG"

        invitee_input = wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "(//app-event-form-modal//app-contact-chips-auto-complete"
                    "//input[@id='inputItem'])[1]",
                )
            )
        )
        safe_click(invitee_input)
        invitee_input.send_keys(EVENT_INVITEE)
        invitee_input.send_keys(Keys.ENTER)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    f"//app-event-form-modal//*[contains(normalize-space(), "
                    f"{json.dumps(EVENT_INVITEE, ensure_ascii=False)})]",
                )
            )
        )

    run_step(enter_invitee, f"وارد کردن مدعو و زدن Enter: {EVENT_INVITEE}")

    def save_event():
        driver.get_log("performance")
        save_button = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//app-event-form-modal//button[@type='submit' and "
                    "(normalize-space()='ذخیره' or .//span[normalize-space()='ذخیره'])]",
                )
            )
        )
        safe_click(save_button)

    run_step(save_event, "کلیک روی دکمه ذخیره")
    run_step(verify_create_event_request, "بررسی پاسخ موفق بک‌اند برای ساخت رویداد")

    if step_failures:
        print(f"\n⚠️ تست تا انتها اجرا شد، اما {len(step_failures)} مرحله خطا داشت:")
        for description, error in step_failures:
            print(f"  - {description}: {error}")
    else:
        print("\n🏁 تست ساخت رویداد با موفقیت و تایید قطعی بک‌اند به پایان رسید.")
finally:
    driver.quit()
