import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ۱. خواندن آدرس سامانه از فایل کانفیگ
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    TARGET_URL = config["url"].strip()
except Exception as e:
    print("❌ فایل config.json یافت نشد!")
    exit()

# ۲. تنظیمات مرورگر و فعال‌سازی شنود شبکه
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--start-maximized")
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=chrome_options)

print("\n🔍 اسکریپت تشخیصی CSRF Token با موفقیت اجرا شد.")
print("🌐 در حال باز کردن سامانه...")
driver.get(TARGET_URL)

print("\n" + "="*60)
print("📌 دستورالعمل:")
print("1. توی مرورگری که باز شده، لاگین کن.")
print("2. یک کاری مثل ارسال ایمیل، ساخت پوشه یا تغییر وضعیت ایمیل انجام بده.")
print("3. بعد از انجام کار، برگرد اینجا و دکمه ENTER رو بزن تا آنالیز شروع بشه.")
print("="*60 + "\n")

input("👉 پس از انجام مراحل بالا، دکمه ENTER را بزنید...")

report = []
report.append("=================== گزارش عیب‌یابی CSRF TOKEN ===================")

# ۳. بررسی کوکی‌ها
report.append("\n--- [1] کوکی‌های مرورگر (Cookies) ---")
try:
    cookies = driver.get_cookies()
    for c in cookies:
        report.append(f"Name: {c.get('name')} | Value: {c.get('value')} | Domain: {c.get('domain')}")
except Exception as e:
    report.append(f"خطا در دریافت کوکی‌ها: {e}")

# ۴. بررسی LocalStorage
report.append("\n--- [2] حافظه محلی (LocalStorage) ---")
try:
    local_storage = driver.execute_script("return window.localStorage;")
    for k, v in local_storage.items():
        report.append(f"Key: {k} -> Value: {v}")
except Exception as e:
    report.append(f"خطا در دریافت LocalStorage: {e}")

# ۵. بررسی SessionStorage
report.append("\n--- [3] حافظه موقت (SessionStorage) ---")
try:
    session_storage = driver.execute_script("return window.sessionStorage;")
    for k, v in session_storage.items():
        report.append(f"Key: {k} -> Value: {v}")
except Exception as e:
    report.append(f"خطا در دریافت SessionStorage: {e}")

# ۶. بررسی تگ‌های متای HTML
report.append("\n--- [4] تگ‌های متای HTML ---")
try:
    metas = driver.find_elements(By.TAG_NAME, "meta")
    found_meta = False
    for m in metas:
        name = m.get_attribute("name") or m.get_attribute("property") or ""
        content = m.get_attribute("content") or ""
        if "csrf" in name.lower() or "token" in name.lower() or "xsrf" in name.lower():
            report.append(f"⭐ Meta Name: {name} | Content: {content}")
            found_meta = True
    if not found_meta:
        report.append("تگ متای مرتبط با CSRF یافت نشد.")
except Exception as e:
    report.append(f"خطا در بررسی تگ‌های meta: {e}")

# ۷. پایش هدرهای شبکه
report.append("\n--- [5] هدرهای درخواست‌های شبکه (Network Request Headers) ---")
try:
    logs = driver.get_log("performance")
    headers_found = False
    for entry in logs:
        try:
            log_data = json.loads(entry["message"])["message"]
            if log_data["method"] == "Network.requestWillBeSent":
                request = log_data["params"]["request"]
                url = request.get("url", "")
                method = request.get("method", "")
                headers = request.get("headers", {})

                # فیلتر کردن فایل‌های استاتیک برای خلوت شدن لاگ
                if not any(ext in url.lower() for ext in [".js", ".css", ".png", ".jpg", ".svg", ".woff", ".ttf", ".ico"]):
                    headers_found = True
                    report.append(f"\n[URL]: {method} {url}")
                    report.append("  [Request Headers]:")
                    for h_key, h_val in headers.items():
                        if any(k in h_key.lower() for k in ["csrf", "xsrf", "token", "auth", "x-"]):
                            report.append(f"    ⭐ {h_key}: {h_val}")
                        else:
                            report.append(f"       {h_key}: {h_val}")
        except:
            pass
    if not headers_found:
        report.append("درخواست API خاصی در شبکه ثبت نشد.")
except Exception as e:
    report.append(f"خطا در تحلیل لاگ شبکه: {e}")

report_text = "\n".join(report)

# ذخیره خروجی در فایل متنی
output_filename = "csrf_debug_report.txt"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write(report_text)

print("\n" + "="*60)
print(f"✅ تحلیل به پایان رسید! گزارش کامل در فایل '{output_filename}' ذخیره شد.")
print("="*60)

driver.quit()