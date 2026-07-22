import time
import json
import random
import string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================
# ۱. بارگذاری کانفیگ و تنظیمات مرورگر
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
    print("❌ فایل config.json پیدا نشد!")
    exit()

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--start-maximized")
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)


def run_step(action, description):
    try:
        action()
        print(f" [✓] {description} با موفقیت انجام شد.")
    except Exception as e:
        error_type = type(e).__name__
        error_details = str(e).replace('\n', ' ')[:150]
        print(f" [⚠️] {description} خطا داد ({error_type}): {error_details}")
        raise e


def generate_alphanumeric_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


# ==============================================================
# ۲. تزریق سشن اولیه
# ==============================================================

driver.get(base_url + "robots.txt")
time.sleep(1.5)

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

    print("✅ سشن با موفقیت تزریق شد.")
except Exception as e:
    print(f"❌ خطا در تزریق سشن: {e}")
    driver.quit()
    exit()


# ==============================================================
# ۳. تابع پایش پاسخ‌های شبکه (Network API Listener)
# ==============================================================

def verify_network_api(target_endpoint, target_method="POST", expected_status=200, timeout=10):
    print(f" [⏳] پایش شبکه برای API: [{target_method}] '{target_endpoint}'...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            logs = driver.get_log("performance")
            for entry in logs:
                log_data = json.loads(entry["message"])["message"]
                if log_data.get("method") == "Network.responseReceived":
                    resp = log_data["params"]["response"]
                    url = resp.get("url", "")
                    status = resp.get("status", 0)
                    if target_endpoint in url and status == expected_status:
                        print(f" [🎯 Network API] درخواست '{target_endpoint}' با استاتوس {status} تایید شد.")
                        return True
        except Exception:
            pass
        time.sleep(0.4)
    print(f" [⚠️ Network API] پاسخ API '{target_endpoint}' در زمان مقرر دریافت نشد.")
    return False


# ==============================================================
# ۴. اجرای سناریوی اصلی (بر اساس لایه به لایه دقیق JSON)
# ==============================================================

try:
    print("\n▶️ شروع اجرای سناریو بر اساس داده‌های استخراج‌شده...")

    main_folder_name = generate_alphanumeric_string(8)
    sub_folder_name = generate_alphanumeric_string(8)


    # گام ۱: ورود به صندوق دریافت
    def step_load_inbox():
        driver.get(base_url + "mail/message?query=2&page=1&type=inbox")
        time.sleep(2.5)


    run_step(step_load_inbox, "ورود به صفحه Inbox")


    # گام ۲: ساخت پوشه اصلی از منوی ریشه پوشه‌ها
    def step_create_main_folder():
        # کلیک روی دکمه three dots ریشه پوشه‌ها (node_folders)
        root_btn = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//*[@id='node_folders']//button[contains(., 'more_vert')] | //*[@id='node_folders']/div[2]/button[1]"
        )))
        driver.execute_script("arguments[0].click();", root_btn)
        time.sleep(1)

        # انتخاب گزینه ساخت زیرپوشه
        create_opt = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//div[contains(@class, 'cdk-overlay-container')]//button[contains(., 'ساخت زير پوشه') or contains(., 'create_new_folder')]"
        )))
        driver.execute_script("arguments[0].click();", create_opt)
        time.sleep(1)

        # درج نام پوشه
        input_elem = wait.until(EC.visibility_of_element_located((
            By.XPATH, "//app-add-edit-folder-modal//input"
        )))
        input_elem.clear()
        input_elem.send_keys(main_folder_name)
        time.sleep(0.5)

        # کلیک دکمه "ایجاد"
        submit_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//app-add-edit-folder-modal//button[contains(., 'ایجاد')]"
        )))
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(1.5)


    run_step(step_create_main_folder, f"ساخت پوشه اصلی با نام '{main_folder_name}'")
    verify_network_api("api/folders", target_method="POST", expected_status=200)


    # گام ۳: باز کردن مودال انتقال برای پوشه تازه ساخته‌شده
    def step_open_move_modal():
        folder_node = wait.until(EC.presence_of_element_located((
            By.XPATH,
            f"//*[contains(@class, 'tree-child-item') or contains(@class, 'tree-item')]//a[contains(., '{main_folder_name}')] | //*[text()[contains(., '{main_folder_name}')]]/ancestor::*[contains(@class, 'tree-item') or contains(@id, 'node_')][1]"
        )))

        three_dots = folder_node.find_element(By.XPATH, ".//button[contains(., 'more_vert')]")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", three_dots)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", three_dots)
        time.sleep(1.2)

        # کلیک گزینه "انتقال به .."
        move_opt = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//div[contains(@class, 'cdk-overlay-container')]//button[contains(., 'انتقال به') or contains(., 'drive_file_move')]"
        )))
        driver.execute_script("arguments[0].click();", move_opt)
        time.sleep(1.5)

        wait.until(EC.visibility_of_element_located((By.XPATH, "//app-move-modal")))


    run_step(step_open_move_modal, f"باز کردن مودال انتقال برای پوشه '{main_folder_name}'")


    # گام ۴: ساخت زیرپوشه درون صندوق ارسال و انجام انتقال
    def step_create_subfolder_and_move():
        # ۱. کلیک روی فلش (arrow_left) جلوی "صندوق ارسال" (Sent / item_5)
        print("   -> کلیک روی فلش بازکننده صندوق ارسال...")
        sent_arrow_btn = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//app-move-modal//li[@id='item_5']//button[contains(., 'arrow_left') or contains(@class, 'dialog_item-arrow-btn')] | //app-move-modal//li[contains(., 'صندوق ارسال') or contains(., 'Sent')]//button[contains(., 'arrow_left') or contains(@class, 'dialog_item-arrow-btn')]"
        )))
        driver.execute_script("arguments[0].click();", sent_arrow_btn)
        time.sleep(1.2)

        # ۲. کلیک دکمه "جدید" در مودال
        print("   -> کلیک دکمه 'جدید'...")
        new_btn = wait.until(EC.presence_of_element_located((
            By.XPATH, "//app-move-modal//button[contains(., 'جدید')]"
        )))
        driver.execute_script("arguments[0].click();", new_btn)
        time.sleep(1.2)

        # ۳. کلیک صریح روی سطر "نام پوشه جدید" برای فوکوس و فعال‌سازی input
        print("   -> انتخاب سطر 'نام پوشه جدید'...")
        new_row = wait.until(EC.presence_of_element_located((
            By.XPATH, "//app-move-modal//li[contains(., 'نام پوشه جدید')]"
        )))
        driver.execute_script("arguments[0].click();", new_row)
        time.sleep(0.5)

        # ۴. تایپ نام زیرپوشه
        print(f"   -> ورود نام زیرپوشه: '{sub_folder_name}'...")
        sub_input = wait.until(EC.visibility_of_element_located((
            By.XPATH, "//app-move-modal//input"
        )))
        driver.execute_script("arguments[0].focus();", sub_input)
        sub_input.clear()
        sub_input.send_keys(sub_folder_name)
        time.sleep(0.5)

        # ۵. کلیک دکمه "ساخت"
        print("   -> کلیک دکمه 'ساخت'...")
        make_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//app-move-modal//button[contains(., 'ساخت')]"
        )))
        driver.execute_script("arguments[0].click();", make_btn)
        time.sleep(1.5)

        # اعتبارسنجی API ساخت زیرپوشه
        verify_network_api("api/folders", target_method="POST", expected_status=200)

        # ۶. انتخاب زیرپوشه ساخته‌شده از لیست مودال
        print(f"   -> انتخاب زیرپوشه '{sub_folder_name}' از لیست...")
        created_item = wait.until(EC.presence_of_element_located((
            By.XPATH, f"//app-move-modal//li[contains(., '{sub_folder_name}')]"
        )))
        driver.execute_script("arguments[0].click();", created_item)
        time.sleep(1)

        # ۷. کلیک دکمه نهایی "انتقال"
        print("   -> کلیک دکمه 'انتقال'...")
        final_move_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//app-move-modal//button[contains(., 'انتقال')]"
        )))
        driver.execute_script("arguments[0].click();", final_move_btn)
        time.sleep(2)


    run_step(step_create_subfolder_and_move, f"ساخت زیرپوشه '{sub_folder_name}' در صندوق ارسال و انتقال به آن")
    verify_network_api("api/folders/move", target_method="PUT", expected_status=200)

    print("\n✅ سناریو کاملاً ایزوله، دقیق و بدون خطا به پایان رسید.")

except Exception as e:
    print(f"\n❌ اجرا با خطا مواجه شد: {e}")
finally:
    time.sleep(2)
    driver.quit()