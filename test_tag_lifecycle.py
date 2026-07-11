import time
import json
import os
import random
import string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

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
actions = ActionChains(driver)


def run_step(action, description):
    try:
        result = action()
        if result != "SKIP_LOG" and not description.startswith("->"):
            print(f"  [✓] {description} با موفقیت انجام شد.")
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f"  [⚠️] {description} خطا داد. علت: {error_msg}")
        raise e  # در این سناریوی پیوسته، اگر یکی خطا بدهد بقیه نباید اجرا شوند


# 🌟 باز کردن یک صفحه خنثی برای جلوگیری از ریدایرکت سریع به لاگین
driver.get(base_url + "robots.txt")
time.sleep(2)

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
    print(f"❌ فایل session.json پیدا نشد یا خطا دارد!")
    driver.quit()
    exit()


# 🌟 نسخه پیشرفته بررسی شبکه: چک کردن متد (POST, PUT, DELETE)
def verify_network_request(api_endpoint, expected_method, timeout=15):
    print(f"    [⏳] در حال بررسی ریکوئست {expected_method} '{api_endpoint}' در شبکه...")
    request_map = {}

    for _ in range(timeout):
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                msg = json.loads(entry["message"])["message"]
                method_name = msg["method"]
                params = msg["params"]

                # ثبت متد ریکوئست هنگام ارسال
                if method_name == "Network.requestWillBeSent":
                    req_id = params.get("requestId")
                    request_map[req_id] = params["request"]["method"]

                # بررسی ریسپانس دریافتی
                elif method_name == "Network.responseReceived":
                    req_id = params.get("requestId")
                    response = params["response"]
                    url = response.get("url", "")
                    status = response.get("status")
                    http_method = request_map.get(req_id, "")

                    if api_endpoint.lower() in url.lower() and http_method == expected_method:
                        clean_url = url.split('?')[0]
                        print(f"      [🌐] شکار شد! URL: {clean_url} | Method: {http_method} | Status: {status}")
                        if status in [200, 201, 204]:
                            return True
                        else:
                            raise Exception(f"بک‌اند ارور داد! وضعیت: {status}")
            except:
                pass
        time.sleep(1)
    raise Exception(f"زمان تمام شد! ریکوئست {expected_method} {api_endpoint} پیدا نشد.")


def flush_network_logs():
    """پاکسازی لاگ‌های قبلی شبکه برای جلوگیری از تداخل"""
    driver.get_log("performance")


# ==============================================================
# بخش ۲: سناریوی اصلی (ساخت، ویرایش نام، ویرایش رنگ و حذف برچسب)
# ==============================================================

try:
    # 🌟 تولید نام‌های رندوم (فقط ترکیب حروف و اعداد - بدون خط تیره یا اسپیس)
    initial_tag_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    renamed_tag_name = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

    current_active_tag = initial_tag_name

    print(f"\n▶️ شروع تست: چرخه حیات کامل برچسب")
    print(f"   - نام اولیه: {initial_tag_name}")
    print(f"   - نام ویرایش شده: {renamed_tag_name}\n")

    # --- ورود به اینباکس برای لود شدن سایدبار ---
    run_step(lambda: driver.get(base_url + 'mail/message?query=2&page=1&type=inbox'), "ورود به اینباکس جهت لود سایدبار")
    time.sleep(5)
    flush_network_logs()


    # -------------------------------------------------------------
    # مرحله ۱: ساخت برچسب جدید
    # -------------------------------------------------------------
    def create_tag():
        # پیدا کردن منوی اصلی برچسب‌ها و کلیک روی سه‌نقطه آن
        main_tags_menu = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//a[.//span[contains(text(), 'برچسب')]]//button | //app-mail-sidebar-item[.//span[contains(text(), 'برچسب')]]//button"
        )))
        driver.execute_script("arguments[0].click();", main_tags_menu)
        time.sleep(1)

        # کلیک روی "ساخت برچسب"
        create_opt = wait.until(EC.presence_of_element_located((
            By.XPATH, "//span[normalize-space()='ساخت برچسب']"
        )))
        driver.execute_script("arguments[0].click();", create_opt)
        time.sleep(1)

        # تایپ نام در مودال
        input_el = wait.until(EC.presence_of_element_located((
            By.XPATH, "//app-tag-modal//input | //input[contains(@id, 'mat-input')]"
        )))
        input_el.clear()
        input_el.send_keys(initial_tag_name)
        time.sleep(0.5)

        # انتخاب یک رنگ دلخواه (بر اساس ریکورد Playwright شما)
        try:
            color_box = driver.find_element(By.XPATH, "//app-tag-modal//div[contains(@class, 'mb-2')]//div[2]")
            driver.execute_script("arguments[0].click();", color_box)
        except:
            pass  # اگر رنگ اجباری نبود رد شو

        time.sleep(0.5)

        # کلیک روی ایجاد
        submit_btn = wait.until(EC.presence_of_element_located((
            By.XPATH, "//button[.//span[normalize-space()='ایجاد']]"
        )))
        driver.execute_script("arguments[0].click();", submit_btn)


    run_step(create_tag, f"ساخت برچسب جدید با نام: {initial_tag_name}")
    run_step(lambda: verify_network_request("/api/tags", "POST"), "بررسی کد 200 برای ریکوئست POST ساخت برچسب")
    time.sleep(2)
    flush_network_logs()


    # -------------------------------------------------------------
    # مرحله ۲: ویرایش نام برچسب
    # -------------------------------------------------------------
    def rename_tag():
        # پیدا کردن آیتم برچسب ساخته شده در سایدبار
        tag_item = wait.until(EC.presence_of_element_located((
            By.XPATH, f"//span[normalize-space()='{current_active_tag}']/ancestor::a"
        )))

        # هاور کردن روی برچسب برای ظاهر شدن دکمه سه‌نقطه
        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));", tag_item)
        time.sleep(0.5)

        tag_more_vert = tag_item.find_element(By.XPATH, ".//button")
        driver.execute_script("arguments[0].click();", tag_more_vert)
        time.sleep(1)

        # کلیک روی آیکون تغییر نام
        rename_opt = wait.until(EC.presence_of_element_located((
            By.XPATH, "//i[normalize-space()='drive_file_rename_outline'] | //span[contains(text(), 'تغییر نام')]"
        )))
        driver.execute_script("arguments[0].click();", rename_opt)
        time.sleep(1)

        # تایپ نام جدید
        input_el = wait.until(EC.presence_of_element_located((
            By.XPATH, "//app-input-dialog//input | //input[@id='inputForm']"
        )))
        input_el.send_keys(Keys.CONTROL + "a")
        input_el.send_keys(Keys.BACKSPACE)
        input_el.send_keys(renamed_tag_name)
        time.sleep(0.5)

        # کلیک روی ذخیره
        save_btn = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//app-input-dialog//button[.//span[normalize-space()='ذخیره']] | //button[.//span[normalize-space()='ذخیره']]"
        )))
        driver.execute_script("arguments[0].click();", save_btn)


    run_step(rename_tag, f"ویرایش نام برچسب به: {renamed_tag_name}")
    run_step(lambda: verify_network_request("/api/tags/rename", "PUT"), "بررسی کد 200 برای ریکوئست PUT تغییر نام")
    current_active_tag = renamed_tag_name
    time.sleep(2)
    flush_network_logs()


    # -------------------------------------------------------------
    # مرحله ۳: تغییر رنگ برچسب
    # -------------------------------------------------------------
    def change_tag_color():
        tag_item = wait.until(EC.presence_of_element_located((
            By.XPATH, f"//span[normalize-space()='{current_active_tag}']/ancestor::a"
        )))

        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));", tag_item)
        time.sleep(0.5)

        tag_more_vert = tag_item.find_element(By.XPATH, ".//button")
        driver.execute_script("arguments[0].click();", tag_more_vert)
        time.sleep(1)

        # منوی رنگ برچسب
        color_menu = wait.until(EC.presence_of_element_located((
            By.XPATH, "//span[contains(text(), 'رنگ برچسب')]"
        )))
        driver.execute_script("arguments[0].click();", color_menu)
        time.sleep(1)

        # انتخاب یکی از رنگ‌ها از پالت
        color_items = wait.until(EC.presence_of_all_elements_located((
            By.XPATH, "//div[contains(@class, 'cdk-overlay-pane')]//span"
        )))
        driver.execute_script("arguments[0].click();", color_items[-1])  # انتخاب رنگ آخر


    run_step(change_tag_color, "تغییر رنگ برچسب")
    run_step(lambda: verify_network_request("/api/tags/update", "PUT"), "بررسی کد 200 برای ریکوئست PUT تغییر رنگ")
    time.sleep(2)
    flush_network_logs()


    # -------------------------------------------------------------
    # مرحله ۴: حذف برچسب
    # -------------------------------------------------------------
    def delete_tag():
        tag_item = wait.until(EC.presence_of_element_located((
            By.XPATH, f"//span[normalize-space()='{current_active_tag}']/ancestor::a"
        )))

        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));", tag_item)
        time.sleep(0.5)

        tag_more_vert = tag_item.find_element(By.XPATH, ".//button")
        driver.execute_script("arguments[0].click();", tag_more_vert)
        time.sleep(1)

        # گزینه حذف
        delete_opt = wait.until(EC.presence_of_element_located((
            By.XPATH, "//span[normalize-space()='حذف'] | //button[.//span[normalize-space()='حذف']]"
        )))
        driver.execute_script("arguments[0].click();", delete_opt)
        time.sleep(1)

        # تایید حذف
        confirm_btn = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//app-confirm-dialog//button[.//span[normalize-space()='تایید']] | //button[.//span[normalize-space()='تایید']]"
        )))
        driver.execute_script("arguments[0].click();", confirm_btn)


    run_step(delete_tag, "حذف نهایی برچسب ایجاد شده")
    run_step(lambda: verify_network_request("/api/tags", "DELETE"), "بررسی کد 200 برای ریکوئست DELETE حذف برچسب")

    print("\n🏁 تست چرخه حیات برچسب‌ها با موفقیت به پایان رسید.")

except Exception as e:
    print(f"\n❌ تست به دلیل خطای فوق متوقف شد.")

finally:
    driver.quit()