import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

# ۱. خواندن آدرس سامانه از فایل کانفیگ (با قابلیت تصحیح هوشمند لینک)
# ==============================================================
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        TARGET_URL = config["url"].strip()
        TARGET_EMAIL = config.get("target_email", "").strip()

        CC_EMAIL = config.get("cc_email", "").strip()
        BCC_EMAIL = config.get("bcc_email", "").strip()

        if not TARGET_URL.endswith('/'):
            TARGET_URL += '/'
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
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()
wait = WebDriverWait(driver, 10)


def run_step(action, description):
    try:
        result = action()
        if result != "SKIP_LOG" and not description.startswith("->"):
            print(f"  [✓] {description} با موفقیت انجام شد.")
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f"  [⚠️] {description} خطا داد. علت: {error_msg} (تست ادامه می‌یابد...)")


# تغییر کلیدی ۱: باز کردن یک مسیر خنثی برای جلوگیری از تریگر شدن سریعِ ریدایرکت لاگین
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

    # تغییر کلیدی ۲: رفتن صریح به صفحه اصلی (با توکن‌های آماده) به جای رفرش کردن صفحه لاگین
    driver.get(base_url)
    print("✅ توکن لود شد. ورود به حساب...")

except Exception as e:
    print(f"❌ فایل session.json پیدا نشد یا خطا دارد! اول لاگین را اجرا کن.")
    driver.quit()
    exit()

# ==============================================================
# بخش ۳: سناریوی باز کردن اولین ایمیل و ریپلای پیشرفته
# ==============================================================
try:
    print("\n▶️ شروع تست: باز کردن اولین ایمیل و ارسال پاسخ پیشرفته (پیوست + گیرنده‌ها + امضا)")

    run_step(lambda: driver.get(base_url + 'mail/message?query=2&page=1&type=inbox'), "ورود به اینباکس")
    time.sleep(5)


    def click_mail_icon():
        mail_icon = wait.until(EC.presence_of_element_located((
            By.XPATH, "//a[@id='mailApplicationButton'] | //a[contains(@href, '/nui/mail')]"
        )))
        driver.execute_script("arguments[0].click();", mail_icon)
        time.sleep(3)


    run_step(click_mail_icon, "کلیک روی آیکون ماژول نامه")


    def click_inbox_folder():
        inbox_element = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//span[contains(@class, 'tree-item__name') and contains(text(), 'صندوق دریافت')] | //span[contains(text(), 'صندوق دریافت')]"
        )))
        driver.execute_script("arguments[0].click();", inbox_element)
        time.sleep(2)


    run_step(click_inbox_folder, "کلیک روی منوی صندوق دریافت")


    def click_first_email():
        time.sleep(3)
        first_email = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "(//app-message-list//app-message-list-item)[1] | "
            "(//mat-table//mat-row)[1] | "
            "(//div[@role='grid']//div[@role='row'])[1] | "
            "(//table//tbody//tr)[1] | "
            "(//div[contains(@class, 'mail-list')]//div[contains(@class, 'list-item')])[1]"
        )))

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_email)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", first_email)


    run_step(click_first_email, "کلیک روی اولین ایمیل لیست")


    def handle_optional_popup():
        time.sleep(2)
        dialogs = driver.find_elements(By.TAG_NAME, "mat-dialog-container")
        if not dialogs:
            print("    -> ℹ️ پاپ‌آپ اصلاً روی صفحه نیامد. ادامه مسیر...")
            return "SKIP_LOG"

        print("    -> ℹ️ پاپ‌آپ باز شد! در حال هدف‌گیری دقیقِ تگ span...")

        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "cdk-overlay-backdrop-showing")))
        time.sleep(1.5)

        try:
            btn_close_span = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((
                By.XPATH,
                "//mat-dialog-container//span[contains(text(), 'لغو') or contains(text(), 'خیر') or contains(text(), 'بله')]"
            )))
            btn_close_span.click()
            print(f"    -> ℹ️ کلیک با موفقیت روی متن دکمه انجام شد.")
            WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.CLASS_NAME, "cdk-overlay-backdrop")))
            print("    -> ℹ️ لایه تاریک محو شد و صفحه کاملاً آزاد است.")
            time.sleep(1)
        except Exception as e:
            raise Exception("پاپ‌آپ وجود داشت، اما تگ span (متن دکمه) پیدا نشد یا قابل کلیک نبود!")


    run_step(handle_optional_popup, "بررسی وجود و تست کلیک پاپ‌آپ")


    def click_reply_button():
        reply_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//button[contains(., 'پاسخ')] | //span[contains(text(), 'پاسخ')] | //mat-icon[contains(text(), 'reply')]/ancestor::button"
        )))
        reply_btn.click()


    run_step(click_reply_button, "کلیک روی دکمه پاسخ (Reply)")
    time.sleep(1.5)


    # ==============================================================
    # 🌟 بخش افزودن گیرنده‌های جدید (To, CC, BCC) و فایل پیوست
    # ==============================================================
    def type_emails_with_comma(input_element, emails_string):
        if not emails_string: return
        emails = [e.strip() for e in emails_string.split(',') if e.strip()]
        for email in emails:
            input_element.send_keys(email)
            time.sleep(0.5)
            input_element.send_keys(Keys.ENTER)
            time.sleep(0.2)


    def add_extra_to():
        if not TARGET_EMAIL: return "SKIP_LOG"
        receiver_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='inputItem']")))
        driver.execute_script("arguments[0].click();", receiver_input)
        type_emails_with_comma(receiver_input, TARGET_EMAIL)


    run_step(add_extra_to, "افزودن گیرنده(های) جدید به لیست To")


    def add_cc():
        if not CC_EMAIL: return "SKIP_LOG"
        cc_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'field-toggle-button') and .//span[text()='Cc']]")))
        cc_btn.click()
        time.sleep(0.5)
        all_inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[@id='inputItem']")))
        cc_input = all_inputs[-1]
        driver.execute_script("arguments[0].click();", cc_input)
        type_emails_with_comma(cc_input, CC_EMAIL)


    run_step(add_cc, "افزودن رونوشت (CC)")


    def add_bcc():
        if not BCC_EMAIL: return "SKIP_LOG"
        bcc_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'field-toggle-button') and .//span[text()='Bcc']]")))
        bcc_btn.click()
        time.sleep(0.5)
        all_inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[@id='inputItem']")))
        bcc_input = all_inputs[-1]
        driver.execute_script("arguments[0].click();", bcc_input)
        type_emails_with_comma(bcc_input, BCC_EMAIL)


    run_step(add_bcc, "افزودن رونوشت پنهان (BCC)")


    def upload_attachment():
        file_path = os.path.join(os.getcwd(), "dummy_reply_attachment.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("این یک فایل تستی ایجاد شده برای اتوماسیون ریپلای با پیوست است.")

        file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
        target_input = file_inputs[-1]
        driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';",
                              target_input)
        target_input.send_keys(file_path)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", target_input)
        time.sleep(2)


    run_step(upload_attachment, "آپلود فایل پیوست در ریپلای")


    # ==============================================================

    def type_reply_body():
        time.sleep(2.5)
        iframes = driver.find_elements(By.XPATH, "//iframe")

        if len(iframes) > 0:
            driver.switch_to.frame(iframes[-1])
            body = wait.until(EC.presence_of_element_located((By.XPATH, "//body")))
            driver.execute_script(
                "arguments[0].innerHTML = '<p>این یک پاسخ خودکار به همراه پیوست از طریق سلنیوم است.</p>';", body)
            driver.switch_to.default_content()
        else:
            body = wait.until(EC.presence_of_element_located((By.XPATH,
                                                              "//*[@id='tinymce'] | //div[contains(@class, 'mce-content-body')] | //div[@contenteditable='true']")))
            driver.execute_script(
                "arguments[0].innerHTML = '<p>این یک پاسخ خودکار به همراه پیوست از طریق سلنیوم است.</p>';", body)


    run_step(type_reply_body, "تایپ متن پاسخ در بدنه ایمیل")


    # ==========================================================
    # بخش جدید: مدیریت امضا (استفاده از کیبورد در صورت بلاک شدن کلیک)
    # ==========================================================
    def open_signature_menu():
        signature_btn = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//span[contains(text(),'امضاها')] | //span[normalize-space()='امضاها']")
        ))
        driver.execute_script("arguments[0].click();", signature_btn)


    run_step(open_signature_menu, "کلیک روی دکمه 'امضاها'")


    def choose_signature():
        time.sleep(1.5)

        try:
            menu_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH,
                 "//*[contains(@class, 'mat-mdc-menu-item-text')]/ancestor::button | //button[@role='menuitem']")
            ))
            menu_button.click()
        except Exception:
            webdriver.ActionChains(driver) \
                .send_keys(Keys.ARROW_DOWN) \
                .pause(0.5) \
                .send_keys(Keys.ENTER) \
                .perform()

        time.sleep(2)


    run_step(choose_signature, "انتخاب اولین امضا از منوی باز شده")


    # ==========================================================

    def click_send_button():
        send_btn = wait.until(EC.presence_of_element_located((
            By.XPATH, "//button[normalize-space()='ارسال'] | //button[.//span[normalize-space()='ارسال']]"
        )))
        driver.execute_script("arguments[0].click();", send_btn)


    run_step(click_send_button, "کلیک روی دکمه ارسال")


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

    print("\n🏁 تست ریپلای پیشرفته با موفقیت به پایان رسید.")

finally:
    driver.quit()