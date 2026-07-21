import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
# بخش ۱: راه‌اندازی و تزریق خودکار سشن (این بخش در تمام تست‌ها ثابت است)

# ۱. تنظیمات برای جلوگیری از بسته شدن خودکار کروم
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--start-maximized") # باز شدن مکسیمایز از همان ابتدا

# راه‌اندازی مرورگر با تنظیمات جدید
driver = webdriver.Chrome(options=chrome_options)

# ۲. زمان انتظار هوشمند (۱۰ ثانیه برای پایداری در لودینگ‌ها)
wait = WebDriverWait(driver, 10)
actions = ActionChains(driver)

# تابع کمکی برای مدیریت مراحل
def do_step(func, step_name):
    try:
        func()
        print(f"  [✓] {step_name} با موفقیت انجام شد.")
    except Exception as e:
        print(f"  [⚠️] {step_name} خطا داد. علت: {str(e)[:50]}...")

# Step 1 & 2: باز کردن صفحه و رفرش
do_step(lambda: driver.get('https://mail.chbeta.ir/nui/auth/login'), "باز کردن سایت")
do_step(lambda: driver.refresh(), "رفرش صفحه")

# Step 3: وارد کردن نام کاربری
def step3():
    el = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'کاربری') or @type='text']")))
    el.clear()
    el.send_keys("chtest")
do_step(step3, "وارد کردن نام کاربری")

# Step 4: وارد کردن رمز عبور
def step4():
    el = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='password']")))
    el.clear()
    el.send_keys("Sa-123456")
do_step(step4, "وارد کردن رمز عبور")


# Step 7: کلیک روی ورود
do_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@id='loginbtn'] | //button[contains(., 'ورود')]"))).click(), "کلیک روی ورود")

# مکث برای باز شدن کامل داشبورد
time.sleep(5)


# تعریف انتظار هوشمند
wait = WebDriverWait(driver, 5)

# 🔍 تغییر مهم: چاپ کردن خطای دقیق برای پیدا کردن مقصر
def run_step(action, description):
    try:
        action()
        print(f"  [✓] {description} با موفقیت انجام شد.")
    except Exception as e:
        # نام و متن خطای سلنیوم رو چاپ می‌کنه
        error_msg = str(e).split('\n')[0]
        print(f"  [⚠️] {description} خطا داد. علت: {error_msg}")


# Step 2: Click on "add_circle_outlineنامه جدید"
run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'نامه جدید')]"))).click(), "Step 2: کلیک روی نامه جدید")
time.sleep(1.5)

# Step 3: Click on "mat-select-value-4"
run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//mat-select[@role='combobox'] | //div[contains(@id,'mat-select-value')]"))).click(), "Step 3: باز کردن منوی فرستنده")

# Step 4: Click on "( chtest@chbeta.ir ) TestZade"
run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//mat-option[contains(., 'TestZade')]"))).click(), "Step 4: انتخاب حساب TestZade")

# Step 5: Click on "combobox"
run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='inputItem']"))).click(), "Step 5: کلیک روی فیلد گیرنده")

# Step 6: Enter "sh" into "combobox"
run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='inputItem']"))).send_keys("sh"), "Step 6: تایپ عبارت sh")
time.sleep(1)

# Step 7: Click on "shayan2 - shayan2@chbeta.ir"
run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'shayan2@chbeta.ir')]"))).click(), "Step 7: انتخاب شایان از لیست")


# ──── تفکیک گام‌ها برای پیدا کردن ارور دقیق ────

def close_dropdown():
    # زدن دکمه Escape برای خلوت شدن صفحه
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(1)
run_step(close_dropdown, "باز شدن فضا (زدن Escape)")

def type_subject():
    # به جای متن، دنبال اینپوت‌های متریال می‌گردیم و آخری (که همیشه موضوع است) را انتخاب می‌کنیم
    inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[contains(@id, 'mat-input')]")))
    target_input = inputs[-1]
    target_input.click()
    target_input.clear()
    target_input.send_keys("aaaaaa")
run_step(type_subject, "تایپ موضوع نامه")

def type_body():
    # بررسی هوشمند: آیا ادیتور داخل iframe است یا مستقیماً در صفحه؟
    iframes = driver.find_elements(By.XPATH, "//iframe")
    if len(iframes) > 0:
        driver.switch_to.frame(iframes[-1])
        body = wait.until(EC.element_to_be_clickable((By.XPATH, "//body")))
        body.click()
        body.send_keys("wqeq")
        driver.switch_to.default_content()
    else:
        body = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='tinymce'] | //div[contains(@class, 'mce-content-body')]")))
        body.click()
        body.send_keys("wqeq")
run_step(type_body, "کلیک روی بدنه متن ایمیل")



# 🎯 ──── اصلاح کلیک روی دکمه ارسال (Step 11) ────

def click_send_button():
    # این XPath فقط دکمه ارسالی رو پیدا می‌کنه که داخل مودال (پنجره نامه) باشه، نه توی منوی کناری!
    send_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//app-new-compose//button[contains(., 'ارسال')] | //app-modal-container//button[.//span[contains(text(), 'ارسال')]]"
    )))
    send_btn.click()

run_step(click_send_button, "Step 11: کلیک روی دکمه ارسال")

# ────────────────────────────────────────────────


print("\n🏁 اسکریپت با موفقیت به پایان رسید.")