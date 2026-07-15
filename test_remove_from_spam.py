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

# ==============================================================
# بخش ۱: خواندن کانفیگ، تنظیمات مرورگر و تزریق سشن
# ==============================================================

try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    TARGET_URL = config["url"].strip()
    if not TARGET_URL.endswith('/'):
        TARGET_URL += '/'
    if not TARGET_URL.endswith('nui/'):
        TARGET_URL += 'nui/'
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
            print(f"  [✓] {description} با موفقیت انجام شد.")
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f"  [⚠️] {description} خطا داد. علت: {error_msg}")


# 🌟 قانون طلایی: ابتدا ورود به مسیر خنثی جهت جلوگیری از ریدایرکت لاگین و ایجاد فرصت پایدار تزریق
driver.get(base_url + "robots.txt")
time.sleep(2)

try:
    if not os.path.exists("session.json"):
        raise FileNotFoundError("فایل session.json پیدا نشد!")

    with open("session.json", "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
        session_data = loaded_data if isinstance(loaded_data, dict) else {}

    cookies = session_data.get("cookies", [])
    if cookies:
        for cookie in cookies:
            driver.add_cookie(cookie)

    local_storage = session_data.get("local_storage", {})
    if isinstance(local_storage, dict):
        for key, value in local_storage.items():
            safe_value = json.dumps(value) if not isinstance(value, str) else f"'{value}'"
            driver.execute_script(f"window.localStorage.setItem('{key}', {safe_value});")

    session_storage = session_data.get("session_storage", {})
    if isinstance(session_storage, dict):
        for key, value in session_storage.items():
            safe_value = json.dumps(value) if not isinstance(value, str) else f"'{value}'"
            driver.execute_script(f"window.sessionStorage.setItem('{key}', {safe_value});")

    driver.refresh()
    print("✅ توکن لود شد. ورود به حساب...")
except Exception as e:
    print(f"❌ خطایی در فرآیند تزریق سشن رخ داد: {str(e)}")
    driver.quit()
    exit()


def verify_network_request(api_endpoint, timeout=15):
    print(f"  [⏳] در حال بررسی ریکوئست '{api_endpoint}' در شبکه...")
    for _ in range(timeout):
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                log_data = json.loads(entry["message"])["message"]
                if log_data["method"] == "Network.responseReceived":
                    response = log_data["params"]["response"]
                    url = response.get("url", "")
                    status = response.get("status")
                    if api_endpoint.lower() in url.lower():
                        clean_url = url.split('?')[0]
                        print(f"  [🌐] شکار شد! URL: {clean_url} | Status: {status}")
                        if status == 200 or status == 204:
                            return True
                        else:
                            raise Exception(f"بک‌اند ارور داد! وضعیت: {status}")
            except Exception as ex:
                if "بک‌اند ارور داد" in str(ex):
                    raise ex
        time.sleep(1)
    raise Exception(f"زمان تمام شد! ریکوئست {api_endpoint} پیدا نشد.")


# ==============================================================
# بخش ۲: سناریوی اصلی (خارج کردن ایمیل از هرزنامه و پایش شبکه)
# ==============================================================

try:
    print("\n▶️ شروع تست: خارج کردن اولین ایمیل از صندوق هرزنامه (Spam)")


    # گام ۱: لود کردن داشبورد اصلی سامانه با استفاده از آدرس پویا
    def load_dashboard():
        driver.get(base_url)
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".splash-screen")))
        except Exception:
            pass
        time.sleep(3)


    run_step(load_dashboard, "لود کردن داشبورد اصلی سامانه")


    # گام ۲: کلیک هدفمند روی هرزنامه (پوشه سایدبار)
    def click_spam_folder():
        selectors = [
            (By.XPATH, "//a[@id='node_4']//span[contains(@class, 'tree-item__name') and contains(text(), 'هرزنامه')]"),
            (By.XPATH, "//span[contains(@class, 'tree-item__name') and contains(text(), 'هرزنامه')]")
        ]

        spam_el = None
        for by_type, selector_val in selectors:
            try:
                spam_el = wait.until(EC.presence_of_element_located((by_type, selector_val)))
                break
            except Exception:
                continue

        if not spam_el:
            raise Exception("منوی هرزنامه در سایدبار پیدا نشد!")

        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            actions = ActionChains(driver)
            actions.move_to_element(spam_el).perform()
        except Exception:
            pass

        driver.execute_script("arguments[0].click();", spam_el)
        time.sleep(4)  # مکث بهینه جهت لود و رندر کامل ایمیل‌ها درون کانتینر جدول


    run_step(click_spam_folder, "کلیک روی منوی هرزنامه (Spam)")


    # گام ۳: کلیک روی دکمه سه نقطه (more_vert) اولین ایمیل واقعی در جدول لیست
    def click_more_actions():
        # 🌟 قرنطینه کامل انتخاب‌گر به جدول اصلی (app-mail-table) جهت جلوگیری از تداخل با سه نقطه‌ی مدیریت پوشه در سایدبار
        selectors = [
            (By.XPATH, "//app-mail-table//tbody/tr[1]//app-table-action-single//button"),
            (By.XPATH, "(//app-mail-table//tbody/tr)[1]//button[contains(@class, 'mdc-icon-button')]"),
            (By.XPATH, "//mat-sidenav-content//table/tbody/tr[1]//button"),
            (By.CSS_SELECTOR, "app-mail-table tbody tr:nth-child(1) button")
        ]

        more_btn = None
        for by_type, selector_val in selectors:
            try:
                more_btn = wait.until(EC.presence_of_element_located((by_type, selector_val)))
                break
            except Exception:
                continue

        if not more_btn:
            raise Exception("دکمه سه نقطه (more_vert) اولین ایمیل در جدول پیدا نشد!")

        driver.execute_script("arguments[0].click();", more_btn)
        time.sleep(1.5)  # مکث هوشمند برای باز شدن بدون انیمیشنِ پاپ‌آپ متریال


    run_step(click_more_actions, "کلیک روی دکمه بیشتر (more_vert) اولین ایمیل هرزنامه")


    # گام ۴: انتخاب گزینه خارج کردن از هرزنامه از منوی باز شده متریال
    def click_remove_from_spam():
        # هدف‌گیری انحصاری در لایه پاپ‌آپ باز شده فرانت (cdk-overlay-container)
        selectors = [
            (By.XPATH,
             "//div[contains(@class, 'cdk-overlay-container')]//span[contains(text(),'خارج کردن از هرزنامه')]"),
            (By.XPATH, "//button[contains(., 'خارج کردن از هرزنامه')]"),
            (By.XPATH, "//span[contains(text(),'خارج کردن از هرزنامه')]")
        ]

        remove_btn = None
        for by_type, selector_val in selectors:
            try:
                remove_btn = wait.until(EC.presence_of_element_located((by_type, selector_val)))
                break
            except Exception:
                continue

        if not remove_btn:
            raise Exception("گزینه 'خارج کردن از هرزنامه' در منوی باز شده پیدا نشد!")

        driver.execute_script("arguments[0].click();", remove_btn)
        time.sleep(2)


    run_step(click_remove_from_spam, "کلیک روی گزینه 'خارج کردن از هرزنامه'")


    # گام ۵: پایش ترافیک شبکه جهت اطمینان از ارسال درخواست PUT به اندپوینت هرزنامه
    def verify_spam_api_call():
        verify_network_request("api/mail/spam")


    run_step(verify_spam_api_call, "بررسی صحت ارسال موفقیت‌آمیز ریکوئست در شبکه")

    print("\n🏁 تست خارج کردن ایمیل از هرزنامه با موفقیت به پایان رسید.")

finally:
    # بستن نهایی درایور برای جلوگیری از مصرف حافظه سیستم
    driver.quit()