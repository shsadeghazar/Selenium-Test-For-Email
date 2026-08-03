import json
import random
import secrets
import string
import time
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# ==============================================================
# ۱. خواندن کانفیگ و ساخت داده‌های تصادفی مخاطب
# ==============================================================
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    TARGET_URL = config["url"].strip()
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


PERSIAN_LETTERS = "ابتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"
ENGLISH_LETTERS = string.ascii_letters
secure_random = random.SystemRandom()


def random_mixed_letters(length):
    """رشته‌ای که حتماً هم حرف فارسی و هم حرف انگلیسی دارد."""
    if length < 2:
        raise ValueError("طول رشتهٔ ترکیبی باید حداقل ۲ باشد")
    chars = [secrets.choice(PERSIAN_LETTERS), secrets.choice(ENGLISH_LETTERS)]
    chars.extend(
        secrets.choice(PERSIAN_LETTERS + ENGLISH_LETTERS)
        for _ in range(length - 2)
    )
    secure_random.shuffle(chars)
    return "".join(chars)


def current_mail_domain(url):
    parsed = urlparse(url if "://" in url else "https://" + url)
    host = (parsed.hostname or "").lower().strip(".")
    for prefix in ("mail.", "webmail.", "email.", "www."):
        if host.startswith(prefix):
            host = host[len(prefix):]
            break
    if not host or "." not in host:
        raise ValueError("دامنهٔ سامانه از مقدار url در config.json قابل تشخیص نیست")
    return host


try:
    MAIL_DOMAIN = current_mail_domain(config["url"].strip())
except ValueError as e:
    print(f"❌ {e}")
    raise SystemExit(1)


CONTACT_DATA = {
    # محدود نگه‌داشتن نام‌ها برای رعایت سقف طول فرم
    "first_name": random_mixed_letters(10),
    "last_name": random_mixed_letters(12),
    "middle_name": random_mixed_letters(10),
    "company": random_mixed_letters(14),
    "job_title": random_mixed_letters(12),
    "email": "test" + "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10)) + "@" + MAIL_DOMAIN,
    "phone": secrets.choice(
        (
            "0910", "0911", "0912", "0913", "0914", "0915", "0916", "0917", "0918", "0919",
            "0920", "0921", "0922", "0930", "0933", "0935", "0936", "0937", "0938", "0939",
            "0990", "0991", "0992", "0993", "0994",
        )
    ) + "".join(secrets.choice(string.digits) for _ in range(7)),
    "address": random_mixed_letters(24),
    "website": "www." + "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12)) + secrets.choice((".ir", ".com", ".net", ".org", ".co.ir")),
    "note": random_mixed_letters(30),
}


def make_updated_contact_data():
    """یک مجموعهٔ کاملاً تازه برای مرحلهٔ ویرایش مخاطب می‌سازد."""
    return {
        "first_name": random_mixed_letters(10),
        "last_name": random_mixed_letters(12),
        "middle_name": random_mixed_letters(10),
        "company": random_mixed_letters(14),
        "job_title": random_mixed_letters(12),
        "email": "test" + "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10)) + "@" + MAIL_DOMAIN,
        "phone": secrets.choice(
            (
                "0910", "0911", "0912", "0913", "0914", "0915", "0916", "0917", "0918", "0919",
                "0920", "0921", "0922", "0930", "0933", "0935", "0936", "0937", "0938", "0939",
                "0990", "0991", "0992", "0993", "0994",
            )
        ) + "".join(secrets.choice(string.digits) for _ in range(7)),
        "address": random_mixed_letters(24),
        "website": "www." + "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12)) + secrets.choice((".ir", ".com", ".net", ".org", ".co.ir")),
        "note": random_mixed_letters(30),
    }


UPDATED_CONTACT_DATA = make_updated_contact_data()


# ==============================================================
# ۲. راه‌اندازی مرورگر و تزریق سشن
#    مطابق الگوی سالم test_reply_with_signature.py
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
# ۳. توابع کمکی
# ==============================================================
def safe_click(element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


def fill(element, value):
    safe_click(element)
    element.clear()
    element.send_keys(value)


def dialog_input_by_label(label_text):
    return wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//app-contact-form-modal//mat-form-field[.//mat-label[normalize-space()="
                + json.dumps(label_text, ensure_ascii=False)
                + "]]//input",
            )
        )
    )


def choose_dialog_select(position, option_text):
    select = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, f"(//app-contact-form-modal//mat-select)[{position}]")
        )
    )
    safe_click(select)
    option = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(
            (By.XPATH, f"//mat-option[.//*[normalize-space()={json.dumps(option_text, ensure_ascii=False)}] or normalize-space()={json.dumps(option_text, ensure_ascii=False)}]")
        )
    )
    safe_click(option)


def is_contact_url(url):
    path = urlparse(url).path.rstrip("/").lower()
    return path.endswith("/api/contacts") or path.endswith("/contacts")


def verify_contact_request(expected_method, action_name, endpoint_kind="contact", timeout=20):
    print(f"  [⏳] در حال پایش شبکه برای {action_name} مخاطب (حداکثر ۲۰ ثانیه)...")
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
                request_method = request_methods.get(request_id, "")

                path = urlparse(url).path.rstrip("/").lower()
                if endpoint_kind == "trash":
                    endpoint_matches = path.endswith("/api/contacts/trash") or path.endswith("/contacts/trash")
                else:
                    endpoint_matches = is_contact_url(url)

                if request_method.upper() != expected_method or not endpoint_matches:
                    continue

                clean_url = url.split("?", 1)[0]
                print(f"  [🌐] ریکوئست {action_name} مخاطب پیدا شد! URL: {clean_url} | Status: {status}")

                if status in (200, 201):
                    print(f"  [✓] تایید قطعی: مخاطب با پاسخ موفق بک‌اند {action_name} شد.")
                    return True

                raise Exception(f"بک‌اند هنگام {action_name} مخاطب خطا داد! کد وضعیت: {status}")
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue

        time.sleep(0.5)

    endpoint_text = "/contacts/trash" if endpoint_kind == "trash" else "/contacts"
    raise Exception(f"زمان انتظار تمام شد! ریکوئست {expected_method} {endpoint_text} برای {action_name} مخاطب در شبکه یافت نشد.")


def contact_row_by_email(email):
    quoted_email = json.dumps(email, ensure_ascii=False)
    return WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//app-contact-row[.//*[normalize-space()=" + quoted_email + "] or contains(normalize-space(.), " + quoted_email + ")]",
            )
        )
    )


def row_action_button(email, icon_name):
    quoted_email = json.dumps(email, ensure_ascii=False)
    quoted_icon = json.dumps(icon_name)

    def find_clickable_action(_driver):
        rows = _driver.find_elements(
            By.XPATH,
            "//app-contact-row[.//*[normalize-space()=" + quoted_email
            + "] or contains(normalize-space(.), " + quoted_email + ")]",
        )
        for row in rows:
            if not row.is_displayed():
                continue
            buttons = row.find_elements(
                By.XPATH,
                ".//button["
                ".//app-font-icon[@name=" + quoted_icon + "] "
                "or .//*[self::i or self::mat-icon][normalize-space()=" + quoted_icon + "] "
                "or normalize-space()=" + quoted_icon +
                "]",
            )
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    return button
        return False

    return WebDriverWait(driver, 8, poll_frequency=0.25).until(
        find_clickable_action
    )


def hovered_row_edit_button(email):
    """روی ردیف مخاطب هاور می‌کند و دکمهٔ edit نمایان‌شده را برمی‌گرداند."""
    quoted_email = json.dumps(email, ensure_ascii=False)

    def hover_and_find_edit(_driver):
        try:
            rows = _driver.find_elements(
                By.XPATH,
                "//app-contact-row[.//*[normalize-space()=" + quoted_email
                + "] or contains(normalize-space(.), " + quoted_email + ")]",
            )
            for row in rows:
                if not row.is_displayed():
                    continue

                _driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    row,
                )
                ActionChains(_driver).move_to_element(row).pause(0.5).perform()

                buttons = row.find_elements(
                    By.XPATH,
                    ".//button[.//app-font-icon[@name='edit']]",
                )
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        return button
        except Exception:
            # در بازسازی ردیف توسط Angular، دور بعدی WebDriverWait
            # ردیف و دکمه را دوباره از DOM می‌گیرد.
            return False
        return False

    return WebDriverWait(driver, 10, poll_frequency=0.25).until(
        hover_and_find_edit
    )


def hovered_row_delete_button(email):
    """روی ردیف مخاطب هاور می‌کند و دکمهٔ delete نمایان‌شده را برمی‌گرداند."""
    quoted_email = json.dumps(email, ensure_ascii=False)

    def hover_and_find_delete(_driver):
        try:
            rows = _driver.find_elements(
                By.XPATH,
                "//app-contact-row[.//*[normalize-space()=" + quoted_email
                + "] or contains(normalize-space(.), " + quoted_email + ")]",
            )
            for row in rows:
                if not row.is_displayed():
                    continue

                _driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    row,
                )
                ActionChains(_driver).move_to_element(row).pause(0.5).perform()

                buttons = row.find_elements(
                    By.XPATH,
                    ".//button[.//app-font-icon[@name='delete']]",
                )
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        return button
        except Exception:
            # در بازسازی ردیف توسط Angular، دور بعدی WebDriverWait
            # ردیف و دکمه را دوباره از DOM می‌گیرد.
            return False
        return False

    return WebDriverWait(driver, 10, poll_frequency=0.25).until(
        hover_and_find_delete
    )


def visible_contact_view_modal(timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-view-modal"))
    )


def visible_modal_action_button(modal, icon_name):
    quoted_icon = json.dumps(icon_name)

    def find_visible_button(_driver):
        buttons = modal.find_elements(
            By.XPATH,
            ".//button["
            ".//app-font-icon[@name=" + quoted_icon + "] "
            "or .//*[self::i or self::mat-icon][normalize-space()=" + quoted_icon + "] "
            "or normalize-space()=" + quoted_icon +
            "]",
        )
        for button in buttons:
            if button.is_displayed() and button.is_enabled():
                return button
        return False

    return WebDriverWait(driver, 10).until(find_visible_button)


def visible_contact_view_edit_button(modal):
    """دکمهٔ edit بخش اصلی مودال را مطابق کلیک ضبط‌شده برمی‌گرداند."""
    desktop_buttons = modal.find_elements(
        By.XPATH,
        ".//div[contains(concat(' ', normalize-space(@class), ' '), ' hide-xs ')]"
        "//button[.//app-font-icon[@name='edit']]",
    )
    for button in desktop_buttons:
        if button.is_displayed() and button.is_enabled():
            return button

    # چیدمان موبایل یا نسخه‌ای از سامانه که کلاس hide-xs ندارد.
    return visible_modal_action_button(modal, "edit")


def click_until_visible(button_getter, target_locator, failure_message, attempts=3):
    """با گرفتن دوبارهٔ المنت، کلیک را تا مشاهدهٔ نتیجهٔ واقعی تکرار می‌کند."""
    last_error = None
    for attempt in range(attempts):
        try:
            button = button_getter()
            if attempt == 0:
                safe_click(button)
            else:
                driver.execute_script("arguments[0].click();", button)

            return WebDriverWait(driver, 6).until(
                EC.visibility_of_element_located(target_locator)
            )
        except Exception as e:
            last_error = e
            time.sleep(0.8)

            # ممکن است کلیک انجام شده باشد ولی انتظار قبلی دقیقاً هم‌زمان
            # با انیمیشن مودال تمام شده باشد.
            visible_targets = driver.find_elements(*target_locator)
            for target in visible_targets:
                if target.is_displayed():
                    return target

    if isinstance(last_error, TimeoutException):
        raise Exception(failure_message)
    raise Exception(f"{failure_message} علت فنی: {str(last_error).splitlines()[0]}")


def fill_contact_form(data, edit_mode=False):
    fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal input[formcontrolname='firstName']"))), data["first_name"])
    fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal input[formcontrolname='lastName']"))), data["last_name"])
    fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal input[formcontrolname='middleName']"))), data["middle_name"])
    fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal input[formcontrolname='company']"))), data["company"])
    fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal input[formcontrolname='jobTitle']"))), data["job_title"])
    fill(dialog_input_by_label("رایانامه"), data["email"])
    fill(dialog_input_by_label("شماره تماس"), data["phone"])
    fill(dialog_input_by_label("نشانی"), data["address"])

    if edit_mode:
        # ترتیب دقیق کلیک‌های ضبط‌شده: ابتدا نوع نشانی، سپس نوع تلفن.
        # در فرم ویرایش، select سوم متعلق به ردیف اضافه و مخفی تلفن است؛
        # select چهارم برچسب نشانی موجود است.
        choose_dialog_select(4, "آدرس محل کار")
        choose_dialog_select(2, "تلفن شرکت")

    fill(dialog_input_by_label("وب سایت"), data["website"])
    fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal textarea[formcontrolname='note']"))), data["note"])


def close_contact_modal_after_save():
    """مودال نمایش مخاطب را که پس از ذخیرهٔ ویرایش باقی می‌ماند می‌بندد."""
    modal = visible_contact_view_modal()

    close_button = visible_modal_action_button(modal, "close")
    safe_click(close_button)
    WebDriverWait(driver, 10).until(EC.invisibility_of_element(modal))


# ==============================================================
# ۴. سناریوی اصلی: ساخت، پیدا کردن، ویرایش، پیدا کردن و حذف مخاطب
# ==============================================================
try:
    print("\n▶️ شروع تست: چرخهٔ کامل ساخت، ویرایش و حذف مخاطب")
    print(f"    رایانامهٔ تصادفی: {CONTACT_DATA['email']}")
    print(f"    شمارهٔ تصادفی: {CONTACT_DATA['phone']}")
    print(f"    وب‌سایت تصادفی: {CONTACT_DATA['website']}")

    def open_inbox():
        driver.get(base_url + "mail/message?query=2&page=1&type=inbox")
        time.sleep(3)

    run_step(open_inbox, "ورود به اینباکس")

    def open_contacts_module():
        contacts_button = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//a[@id='contactApplicationButton'] | //a[contains(@href, '/nui/contacts')]",
                )
            )
        )
        safe_click(contacts_button)
        WebDriverWait(driver, 10).until(EC.url_contains("/contacts"))
        time.sleep(2)

    run_step(open_contacts_module, "کلیک روی آیکون دفترچه نشانی")

    def click_new_contact():
        button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[.//span[normalize-space()='مخاطب جدید']] | //button[contains(normalize-space(.), 'مخاطب جدید')]",
                )
            )
        )
        safe_click(button)
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//app-contact-form-modal"))
        )

    run_step(click_new_contact, "کلیک روی دکمه مخاطب جدید")

    run_step(
        lambda: fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal input[formcontrolname='firstName']"))), CONTACT_DATA["first_name"]),
        "وارد کردن نام تصادفی فارسی و انگلیسی",
    )
    run_step(
        lambda: fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal input[formcontrolname='lastName']"))), CONTACT_DATA["last_name"]),
        "وارد کردن نام خانوادگی تصادفی فارسی و انگلیسی",
    )
    run_step(
        lambda: fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal input[formcontrolname='middleName']"))), CONTACT_DATA["middle_name"]),
        "وارد کردن نام میانی تصادفی فارسی و انگلیسی",
    )
    run_step(
        lambda: fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal input[formcontrolname='company']"))), CONTACT_DATA["company"]),
        "وارد کردن نام شرکت تصادفی فارسی و انگلیسی",
    )
    run_step(
        lambda: fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal input[formcontrolname='jobTitle']"))), CONTACT_DATA["job_title"]),
        "وارد کردن عنوان شغل تصادفی فارسی و انگلیسی",
    )

    run_step(lambda: choose_dialog_select(1, "مخاطبین پیش‌فرض"), "انتخاب دفترچه مخاطبین پیش‌فرض")
    run_step(lambda: fill(dialog_input_by_label("رایانامه"), CONTACT_DATA["email"]), "وارد کردن رایانامهٔ تصادفی روی دامنه سامانه")
    run_step(lambda: fill(dialog_input_by_label("شماره تماس"), CONTACT_DATA["phone"]), "وارد کردن شماره تلفن همراه معتبر ایرانی")
    run_step(lambda: choose_dialog_select(2, "تلفن همراه"), "انتخاب برچسب تلفن همراه")
    run_step(lambda: fill(dialog_input_by_label("نشانی"), CONTACT_DATA["address"]), "وارد کردن نشانی تصادفی فارسی و انگلیسی")
    run_step(lambda: choose_dialog_select(3, "آدرس خانه"), "انتخاب برچسب آدرس خانه")
    run_step(lambda: fill(dialog_input_by_label("وب سایت"), CONTACT_DATA["website"]), "وارد کردن وب‌سایت تصادفی")
    run_step(
        lambda: fill(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal textarea[formcontrolname='note']"))), CONTACT_DATA["note"]),
        "وارد کردن یادداشت تصادفی فارسی و انگلیسی",
    )

    # حذف لاگ‌های شبکهٔ مراحل قبلی تا فقط درخواست ذخیره بررسی شود.
    driver.get_log("performance")

    def save_contact():
        form_modal = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "app-contact-form-modal"))
        )
        save_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//app-contact-form-modal//button[.//span[normalize-space()='ذخیره']] | //app-contact-form-modal//button[normalize-space()='ذخیره']",
                )
            )
        )
        safe_click(save_button)
        WebDriverWait(driver, 15).until(EC.invisibility_of_element(form_modal))

    save_ok = run_step(save_contact, "کلیک روی دکمه ذخیره")
    create_network_ok = run_step(
        lambda: verify_contact_request("POST", "ساخت"),
        "تأیید ریکوئست شبکه ساخت مخاطب",
    ) if save_ok else False

    # ----------------------------------------------------------
    # پیدا کردن همان مخاطب با رایانامهٔ یکتا و ورود به ویرایش
    # ----------------------------------------------------------
    find_created_ok = run_step(
        lambda: contact_row_by_email(CONTACT_DATA["email"]),
        "پیدا کردن مخاطب ساخته‌شده با رایانامهٔ خودش",
    ) if create_network_ok else False

    def open_created_contact_view():
        click_until_visible(
            lambda: hovered_row_edit_button(CONTACT_DATA["email"]),
            (By.CSS_SELECTOR, "app-contact-view-modal"),
            "پس از کلیک edit ردیف، پنجرهٔ نمایش مخاطب باز نشد.",
        )

    contact_view_open_ok = run_step(
        open_created_contact_view,
        "کلیک روی edit ردیف همان مخاطب و باز کردن پنجرهٔ نمایش",
    ) if find_created_ok else False

    def open_created_contact_edit_form():
        def modal_edit_button():
            return visible_contact_view_edit_button(visible_contact_view_modal())

        click_until_visible(
            modal_edit_button,
            (By.CSS_SELECTOR, "app-contact-form-modal"),
            "پس از کلیک edit داخل پنجرهٔ مخاطب، فرم ویرایش باز نشد.",
        )

    edit_open_ok = run_step(
        open_created_contact_edit_form,
        "کلیک روی edit داخل پنجره و باز کردن فرم ویرایش",
    ) if contact_view_open_ok else False

    if edit_open_ok:
        print(f"    رایانامهٔ جدید: {UPDATED_CONTACT_DATA['email']}")
        print(f"    شمارهٔ جدید: {UPDATED_CONTACT_DATA['phone']}")
        print(f"    وب‌سایت جدید: {UPDATED_CONTACT_DATA['website']}")

    edit_fields_ok = run_step(
        lambda: fill_contact_form(UPDATED_CONTACT_DATA, edit_mode=True),
        "ویرایش تمام فیلدهای مخاطب با مقادیر تصادفی جدید",
    ) if edit_open_ok else False

    driver.get_log("performance")

    update_save_ok = run_step(save_contact, "کلیک روی ذخیره پس از ویرایش") if edit_fields_ok else False
    update_network_ok = run_step(
        lambda: verify_contact_request("PUT", "ویرایش"),
        "تأیید ریکوئست شبکه ویرایش مخاطب",
    ) if update_save_ok else False

    # ----------------------------------------------------------
    # بستن نمایش مخاطب، پیدا کردن نسخهٔ ویرایش‌شده و حذف همان رکورد
    # ----------------------------------------------------------
    update_modal_closed_ok = run_step(
        close_contact_modal_after_save,
        "بستن پنجرهٔ نمایش مخاطب ویرایش‌شده",
    ) if update_network_ok else False

    find_updated_ok = run_step(
        lambda: contact_row_by_email(UPDATED_CONTACT_DATA["email"]),
        "پیدا کردن دوبارهٔ مخاطب با رایانامهٔ ویرایش‌شده",
    ) if update_modal_closed_ok else False

    driver.get_log("performance")

    def delete_updated_contact():
        safe_click(hovered_row_delete_button(UPDATED_CONTACT_DATA["email"]))
        confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//app-confirm-dialog//button[normalize-space()='تایید' or .//span[normalize-space()='تایید']]",
                )
            )
        )
        safe_click(confirm_button)

    delete_click_ok = run_step(
        delete_updated_contact,
        "حذف همان مخاطب و تأیید پیام حذف",
    ) if find_updated_ok else False
    delete_network_ok = run_step(
        lambda: verify_contact_request("PUT", "حذف", endpoint_kind="trash"),
        "تأیید ریکوئست شبکه حذف مخاطب",
    ) if delete_click_ok else False

    if create_network_ok and update_network_ok and delete_network_ok:
        print("\n✅ چرخهٔ کامل ساخت، ویرایش و حذف مخاطب با موفقیت انجام شد.")
    else:
        print("\n⚠️ تست تا پایان اجرا شد، اما یک یا چند بخش چرخه به‌طور قطعی تأیید نشد.")

    if step_failures:
        print("\nخلاصه خطاهای مراحل:")
        for description, error in step_failures:
            print(f"  - {description}: {error}")

except Exception as e:
    print(f"\n❌ خطای کلی در تست چرخهٔ مخاطب: {str(e).splitlines()[0]}")

finally:
    driver.quit()
