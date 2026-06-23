import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================
# بخش ۱: خواندن کانفیگ، تنظیمات مرورگر و تزریق سشن
# ==============================================================
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        TARGET_URL = config["url"].strip()
        TARGET_EMAIL = config.get("target_email", "shayan2@chbeta.ir").strip()

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
            print(f"  [✓] {description} با موفقیت انجام شد.")
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f"  [⚠️] {description} خطا داد. علت: {error_msg}")
        raise e

driver.get(base_url)
try:
    with open("session.json", "r", encoding="utf-8") as f: session_data = json.load(f)
    for cookie in session_data.get("cookies", []): driver.add_cookie(cookie)
    for key, value in session_data.get("local_storage", {}).items():
        safe_value = json.dumps(value) if not isinstance(value, str) else f"'{value}'"
        driver.execute_script(f"window.localStorage.setItem('{key}', {safe_value});")
    for key, value in session_data.get("session_storage", {}).items():
        safe_value = json.dumps(value) if not isinstance(value, str) else f"'{value}'"
        driver.execute_script(f"window.sessionStorage.setItem('{key}', {safe_value});")
    driver.refresh()
    print("✅ توکن لود شد. ورود به حساب...")
except Exception as e:
    print(f"❌ فایل session.json پیدا نشد یا خطا دارد!")
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
                        print(f"    [🌐] شکار شد! URL: {clean_url} | Status: {status}")
                        if status == 200: return True
                        elif status == 204: continue
                        else: raise Exception(f"بک‌اند ارور داد! وضعیت: {status}")
            except: pass
        time.sleep(1)
    raise Exception(f"زمان تمام شد! ریکوئست {api_endpoint} پیدا نشد.")

print(f"\n▶️ شروع تست: ارسال نامه جدید همراه با پیوست به {TARGET_EMAIL}")

def click_new_email():
    driver.get(base_url + 'mail/message?query=2&page=1&type=inbox')
    try: wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".splash-screen")))
    except: pass
    time.sleep(2)
    new_mail_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'نامه جدید')]")))
    driver.execute_script("arguments[0].click();", new_mail_btn)

run_step(click_new_email, "کلیک روی نامه جدید و عبور از لودینگ")
time.sleep(1.5)

def check_and_select_from():
    elements = driver.find_elements(By.XPATH, "//mat-select[@role='combobox'] | //div[contains(@id,'mat-select-value')]")
    visible_dropdown = next((el for el in elements if el.is_displayed()), None)
    if not visible_dropdown:
        print("  [ℹ️] فیلد فرستنده (From) وجود نداشت. ادامه عملیات...")
        return "SKIP_LOG"
    try:
        visible_dropdown.click()
        time.sleep(0.5)
        option = wait.until(EC.presence_of_element_located((By.XPATH, "(//mat-option)[1] | //mat-option[contains(., 'TestZade')]")))
        driver.execute_script("arguments[0].click();", option)
    except Exception as e:
        raise Exception("فیلد فرستنده در صفحه هست اما قابل کلیک یا انتخاب نیست!")

run_step(check_and_select_from, "بررسی و انتخاب حساب فرستنده (اختیاری)")


def type_receiver_and_enter():
    # بازگشت به ساختار اصلی شما (جاوااسکریپت کلیک) برای دور زدن لودینگ‌ها
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
    target_input.send_keys("تست ارسال فایل پیوست با اسکریپت پویا")

run_step(type_subject, "تایپ موضوع")

def type_body():
    iframes = driver.find_elements(By.XPATH, "//iframe")
    if len(iframes) > 0:
        driver.switch_to.frame(iframes[-1])
        body = wait.until(EC.presence_of_element_located((By.XPATH, "//body")))
        driver.execute_script("arguments[0].innerHTML = '<p>این نامه حاوی یک فایل پیوست است.</p>';", body)
        driver.switch_to.default_content()
    else:
        body = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='tinymce'] | //div[contains(@class, 'mce-content-body')]")))
        driver.execute_script("arguments[0].innerHTML = '<p>این نامه حاوی یک فایل پیوست است.</p>';", body)

run_step(type_body, "تایپ بدنه")

def upload_file():
    file_path = os.path.join(os.getcwd(), "dummy_test_attachment.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("این یک فایل تستی ایجاد شده توسط اتوماسیون سلنیوم است.")

    file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
    target_input = file_inputs[-1]
    driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';", target_input)
    target_input.send_keys(file_path)
    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", target_input)

run_step(upload_file, "آپلود فایل و بیدار کردن رویداد سایت")
run_step(lambda: verify_network_request("file"), "بررسی کد 200 برای آپلود پیوست (file)")

def click_send():
    send_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[normalize-space()='ارسال'] | //button[.//span[normalize-space()='ارسال']]")))
    driver.execute_script("arguments[0].click();", send_btn)

run_step(click_send, "کلیک روی دکمه ارسال")
run_step(lambda: verify_network_request("/api/mail/send"), "بررسی کد 200 برای ارسال نهایی (send)")

print("\n🏁 تست ارسال با پیوست با موفقیت و تاییدیه قطعی بک‌اند به پایان رسید.")
driver.quit()
