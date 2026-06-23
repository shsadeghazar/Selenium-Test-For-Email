import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

# ۱. خواندن آدرس سامانه و ایمیل هدف از فایل کانفیگ
# ==============================================================
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        TARGET_URL = config["url"].strip()
        TARGET_EMAIL = config.get("target_email", "shayan2@chbeta.ir").strip()

        if not TARGET_URL.endswith('/'):
            TARGET_URL += '/'
        if not TARGET_URL.endswith('nui/'):
            TARGET_URL += 'nui/'

        base_url = TARGET_URL
except FileNotFoundError:
    print("❌ فایل config.json پیدا نشد! لطفاً تست‌ها را از طریق رابط کاربری (UI) اجرا کنید.")
    exit()

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
        print(f"  [⚠️] {description} خطا داد. علت: {error_msg}")
        raise e


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
# بخش ۳: بدنه اصلی تست
# ==============================================================
print(f"\n▶️ شروع تست: ارسال نامه جدید به {TARGET_EMAIL}")

run_step(lambda: driver.get(base_url + 'mail/message?query=2&page=1&type=inbox'), "ورود به اینباکس")
time.sleep(5)

run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'نامه جدید')]"))).click(),
         "کلیک روی نامه جدید")
time.sleep(1.5)


def check_and_select_from():
    elements = driver.find_elements(By.XPATH,
                                    "//mat-select[@role='combobox'] | //div[contains(@id,'mat-select-value')]")
    visible_dropdown = next((el for el in elements if el.is_displayed()), None)

    if not visible_dropdown:
        print("  [ℹ️] فیلد فرستنده (From) وجود نداشت. ادامه عملیات...")
        return "SKIP_LOG"

    try:
        visible_dropdown.click()
        time.sleep(0.5)
        option = wait.until(
            EC.presence_of_element_located((By.XPATH, "(//mat-option)[1] | //mat-option[contains(., 'TestZade')]")))
        driver.execute_script("arguments[0].click();", option)
    except Exception as e:
        raise Exception("فیلد فرستنده وجود دارد اما قابل کلیک یا انتخاب نیست!")


run_step(check_and_select_from, "بررسی و انتخاب حساب فرستنده (اختیاری)")


def type_receiver_and_enter():
    # استفاده از ساختار اصلی شما (کلیک جاوااسکریپتی) برای دور زدن لودینگ
    receiver_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='inputItem']")))
    driver.execute_script("arguments[0].click();", receiver_input)
    receiver_input.send_keys(TARGET_EMAIL)
    time.sleep(1)
    receiver_input.send_keys(Keys.ENTER)


run_step(type_receiver_and_enter, f"تایپ گیرنده و زدن اینتر ({TARGET_EMAIL})")


def type_subject():
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(1)
    inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[contains(@id, 'mat-input')]")))
    target_input = inputs[-1]
    target_input.click()
    target_input.clear()
    target_input.send_keys("تست ارسال از اسکریپت با ایمیل پویا")


run_step(type_subject, "تایپ موضوع نامه")


def type_body():
    iframes = driver.find_elements(By.XPATH, "//iframe")
    if len(iframes) > 0:
        driver.switch_to.frame(iframes[-1])
        body = wait.until(EC.element_to_be_clickable((By.XPATH, "//body")))
        body.click()
        body.send_keys("این یک متن تستی است که به صورت خودکار ارسال شده است.")
        driver.switch_to.default_content()
    else:
        body = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='tinymce'] | //div[contains(@class, 'mce-content-body')]")))
        body.click()
        body.send_keys("این یک متن تستی است که به صورت خودکار ارسال شده است.")


run_step(type_body, "تایپ بدنه ایمیل")


def click_send_button():
    send_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "//app-new-compose//button[contains(., 'ارسال')] | //app-modal-container//button[.//span[contains(text(), 'ارسال')]]"
    )))
    send_btn.click()


run_step(click_send_button, "کلیک روی ارسال")


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
                    if "/api/mail/send" in url.lower():
                        clean_url = url.split('?')[0]
                        print(f"  [🌐] ریکوئست هدف پیدا شد! URL: {clean_url} | Status: {status}")
                        if status == 200:
                            return
                        elif status == 204:
                            continue
                        else:
                            raise Exception(f"بک‌اند ارور داد! کد وضعیت سرور: {status}")
            except Exception:
                pass
        time.sleep(1)
    raise Exception("زمان انتظار تمام شد! ریکوئست اصلی یافت نشد.")


run_step(verify_network_200, "بررسی کد 200 در تب Network")

print("\n🏁 تست با موفقیت به پایان رسید.")
driver.quit()
