import time
import json
import random
import string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================
# ۱. خواندن کانفیگ و تنظیمات مرورگر
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
            print(f"  [✓] {description}")
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f"  [⚠️] {description} خطا داد: {error_msg}")
        raise e


# ==============================================================
# ۲. تزریق سشن و ورود به سامانه
# ==============================================================
# 🌟 باز کردن یک صفحه خنثی برای جلوگیری از ریدایرکت سریع به لاگین و اعمال مکث
driver.get(base_url + "robots.txt")
time.sleep(2)

try:
    with open("session.json", "r", encoding="utf-8") as f:
        session_data = json.load(f)
    for cookie in session_data.get("cookies", []):
        driver.add_cookie(cookie)
    for key, value in session_data.get("local_storage", {}).items():
        safe_val = json.dumps(value) if not isinstance(value, str) else f"'{value}'"
        driver.execute_script(f"window.localStorage.setItem('{key}', {safe_val});")
    for key, value in session_data.get("session_storage", {}).items():
        safe_val = json.dumps(value) if not isinstance(value, str) else f"'{value}'"
        driver.execute_script(f"window.sessionStorage.setItem('{key}', {safe_val});")
    driver.refresh()
    print("✅ توکن لود شد. ورود به حساب...")
except Exception:
    print("❌ فایل session.json پیدا نشد! اول لاگین را اجرا کن.")
    driver.quit()
    exit()


# ==============================================================
# توابع کمکی
# ==============================================================
def verify_api_status(api_endpoint, expect_success=True, timeout=10):
    status_type = "موفقیت‌آمیز (200)" if expect_success else "خطای موردانتظار (400 یا 500)"
    print(f"  [⏳] در حال پایش شبکه برای ریکوئست '{api_endpoint}' با انتظار: {status_type}...")

    end_time = time.time() + timeout
    while time.time() < end_time:
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
                        if status == 204:
                            continue

                        if expect_success:
                            if status in [200, 201]:
                                return True
                            else:
                                raise Exception(f"باید موفق می‌شد اما سرور ارور داد! وضعیت: {status}")
                        else:
                            # 🌟 ثبت خطای تکراری به عنوان موفقیت
                            if status >= 400:
                                print(f"    [ℹ️] عالی! سرور به درستی جلوی نام تکراری را گرفت (کد {status} دریافت شد).")
                                return True
                            else:
                                raise Exception(f"باگ امنیتی! سرور پوشه تکراری را قبول کرد و وضعیت {status} برگرداند.")
            except:
                pass
        time.sleep(0.5)
    raise Exception(f"زمان تمام شد! ریکوئست {api_endpoint} پیدا نشد.")


def generate_random_name(prefix="Test"):
    return prefix + ''.join(random.choices(string.ascii_letters + string.digits, k=5))


# ==============================================================
# ۳. سناریوی اصلی: چرخه حیات پوشه (ساخت، تکرار، ویرایش نام، حذف)
# ==============================================================
print("\n▶️ شروع تست: چرخه حیات پوشه‌ها زیرمجموعه صندوق ارسال")


def load_inbox():
    driver.get(base_url + 'mail/message?query=2&page=1&type=inbox')
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".splash-screen")))
    except:
        pass
    time.sleep(2)


run_step(load_inbox, "لود کردن صفحه اصلی و عبور از صفحه لودینگ")


def attempt_to_create_folder(parent_menu_xpath, folder_name):
    def open_menu():
        menu_btn = wait.until(EC.presence_of_element_located((By.XPATH, parent_menu_xpath)))
        driver.execute_script("arguments[0].click();", menu_btn)

    run_step(open_menu, "باز کردن منوی پوشه والد (صندوق ارسال)")
    time.sleep(1)

    def click_create():
        create_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'ساخت زير پوشه')]")))
        driver.execute_script("arguments[0].click();", create_btn)

    run_step(click_create, "کلیک روی 'ساخت زير پوشه'")
    time.sleep(1.5)

    def enter_name():
        inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[contains(@id, 'mat-input')]")))
        for inp in reversed(inputs):
            if inp.is_displayed():
                inp.click()
                inp.clear()
                inp.send_keys(folder_name)
                inp.send_keys(Keys.TAB)
                break

    run_step(enter_name, f"تایپ نام پوشه: {folder_name}")
    time.sleep(1)

    def submit():
        create_spans = driver.find_elements(By.XPATH, "//span[normalize-space()='ایجاد']")
        clicked = False
        for span in reversed(create_spans):
            if span.is_displayed():
                try:
                    span.click()
                except:
                    driver.execute_script("arguments[0].click();", span)
                clicked = True
                break

        if not clicked:
            raise Exception("دکمه 'ایجاد' پیدا یا کلیک نشد!")

    run_step(submit, "کلیک روی دکمه 'ایجاد'")


def rename_folder(old_name, new_name):
    def open_folder_menu():
        folder_item = wait.until(EC.presence_of_element_located((
            By.XPATH, f"//span[normalize-space()='{old_name}']/ancestor::a | //span[normalize-space()='{old_name}']/ancestor::app-sidebar-menu-item"
        )))
        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));", folder_item)
        time.sleep(0.5)
        menu_btn = folder_item.find_element(By.XPATH, ".//button")
        driver.execute_script("arguments[0].click();", menu_btn)

    run_step(open_folder_menu, f"باز کردن منوی پوشه '{old_name}'")
    time.sleep(1)

    def click_rename():
        rename_opt = wait.until(EC.presence_of_element_located((
            By.XPATH, "//span[contains(text(), 'تغيير نام') or contains(text(), 'تغییر نام')]"
        )))
        driver.execute_script("arguments[0].click();", rename_opt)

    run_step(click_rename, "کلیک روی 'تغيير نام'")
    time.sleep(1)

    def submit_new_name():
        inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[contains(@id, 'mat-input') or contains(@id, 'inputForm')]")))
        for inp in reversed(inputs):
            if inp.is_displayed():
                inp.click()
                inp.send_keys(Keys.CONTROL + "a")
                inp.send_keys(Keys.BACKSPACE)
                inp.send_keys(new_name)
                break
        time.sleep(0.5)
        edit_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[.//span[normalize-space()='ویرایش']]")))
        driver.execute_script("arguments[0].click();", edit_btn)

    run_step(submit_new_name, f"تایپ نام جدید '{new_name}' و ثبت")


def delete_folder(folder_name):
    def open_folder_menu():
        folder_item = wait.until(EC.presence_of_element_located((
            By.XPATH, f"//span[normalize-space()='{folder_name}']/ancestor::a | //span[normalize-space()='{folder_name}']/ancestor::app-sidebar-menu-item"
        )))
        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));", folder_item)
        time.sleep(0.5)
        menu_btn = folder_item.find_element(By.XPATH, ".//button")
        driver.execute_script("arguments[0].click();", menu_btn)

    run_step(open_folder_menu, f"باز کردن منوی پوشه '{folder_name}'")
    time.sleep(1)

    def click_delete():
        delete_opt = wait.until(EC.presence_of_element_located((
            By.XPATH, "//span[normalize-space()='حذف'] | //span[contains(text(), 'حذف')]"
        )))
        driver.execute_script("arguments[0].click();", delete_opt)

    run_step(click_delete, "کلیک روی 'حذف'")
    time.sleep(1)

    def confirm_delete():
        confirm_btn = wait.until(EC.presence_of_element_located((
            By.XPATH, "//button[.//span[normalize-space()='تایید']]"
        )))
        driver.execute_script("arguments[0].click();", confirm_btn)

    run_step(confirm_delete, "کلیک روی تایید حذف")


try:
    # 🌟 استفاده از متن صریح (ارسال) به جای ایندکس برای جلوگیری از خطای پیدا کردن منوی اشتباه
    target_menu_xpath = "//span[contains(text(), 'ارسال')]/ancestor::li//button | //span[contains(text(), 'ارسال')]/ancestor::a//button"

    test_folder_name = generate_random_name()

    print(f"\n--- فاز اول: ساخت پوشه جدید ({test_folder_name}) ---")
    driver.get_log("performance")  # پاکسازی لاگ شبکه
    attempt_to_create_folder(target_menu_xpath, test_folder_name)
    run_step(lambda: verify_api_status("folder", expect_success=True), "تایید API (وضعیت 200) برای بار اول")
    time.sleep(2)

    print(f"\n--- فاز دوم: تلاش مجدد برای ساخت پوشه با همان نام ({test_folder_name}) ---")
    driver.get_log("performance")  # پاکسازی لاگ شبکه
    attempt_to_create_folder(target_menu_xpath, test_folder_name)

    # 🌟 در اینجا دریافت ارور، به عنوان موفقیت ثبت می‌شود
    run_step(lambda: verify_api_status("folder", expect_success=False),
             "تایید دریافت خطای موردانتظار از سرور برای نام تکراری (موفقیت تست)")

    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(2)  # مکث برای بسته شدن کامل مودال قبلی

    # 🌟 فاز سوم: ویرایش نام پوشه‌ای که ساختیم
    renamed_folder_name = generate_random_name("Renamed")
    print(f"\n--- فاز سوم: ویرایش نام پوشه از ({test_folder_name}) به ({renamed_folder_name}) ---")
    driver.get_log("performance")  # پاکسازی لاگ شبکه
    rename_folder(test_folder_name, renamed_folder_name)
    run_step(lambda: verify_api_status("folders/rename", expect_success=True), "تایید دریافت ریکوئست PUT برای folders/rename")
    time.sleep(2)

    # 🌟 فاز چهارم: حذف پوشه‌ای که تغییر نام دادیم
    print(f"\n--- فاز چهارم: انتقال به زباله‌دان / حذف پوشه ({renamed_folder_name}) ---")
    driver.get_log("performance")  # پاکسازی لاگ شبکه
    delete_folder(renamed_folder_name)
    run_step(lambda: verify_api_status("folders/trash", expect_success=True), "تایید دریافت ریکوئست PUT برای folders/trash")

    print("\n✅✅ تست با موفقیت به پایان رسید. سیستم در برابر نام‌های تکراری ایمن است و چرخه حیات کامل پوشه به درستی طی شد!")

except Exception as e:
    print(f"\n❌ عملیات متوقف شد. خطا: {e}")

driver.quit()