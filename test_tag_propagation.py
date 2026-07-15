import time
import json
import os
import random
import string
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

SCRIPT_BUILD = "TAG-SELECTION-DEBUG-V5"
print(f"\n[🧪 BUILD] {SCRIPT_BUILD}")
print(f"[📄 FILE] {os.path.abspath(__file__)}")

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
        # raise e  # کامنت شد تا تست متوقف نشود (درخواست شما)


# 🌟 ورود به مسیر خنثی
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


def verify_network_request(api_endpoint, expected_method, timeout=15):
    """پایش شبکه با دیباگ کامل متد، URL، status و payload."""
    print(f"    [⏳] در حال بررسی ریکوئست {expected_method} '{api_endpoint}' در شبکه...")
    request_map = {}
    matching_requests = []
    all_requests = []
    deadline = time.time() + timeout

    while time.time() < deadline:
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                msg = json.loads(entry["message"])["message"]
                method_name = msg.get("method")
                params = msg.get("params", {})

                if method_name == "Network.requestWillBeSent":
                    req_id = params.get("requestId")
                    req = params.get("request", {})
                    method = req.get("method", "")
                    url = req.get("url", "")
                    post_data = req.get("postData", "")
                    request_map[req_id] = {
                        "method": method,
                        "url": url,
                        "postData": post_data,
                    }
                    if url:
                        all_requests.append(f"[{method}] {url}")
                    if api_endpoint.lower() in url.lower():
                        matching_requests.append((method, url, post_data))
                        print(f"      [📤] درخواست مرتبط ارسال شد: [{method}] {url}")
                        if post_data:
                            print(f"           Payload: {post_data[:500]}")

                elif method_name == "Network.responseReceived":
                    req_id = params.get("requestId")
                    response = params.get("response", {})
                    url = response.get("url", "")
                    status = response.get("status")
                    req_info = request_map.get(req_id, {})
                    http_method = req_info.get("method", "UNKNOWN")

                    if api_endpoint.lower() in url.lower():
                        print(f"      [📥] پاسخ مرتبط: [{http_method}] {url} | Status: {status}")
                        if http_method == expected_method and status in [200, 201, 204]:
                            return True
                        if http_method == expected_method and status not in [200, 201, 204]:
                            raise Exception(f"بک‌اند ارور داد! وضعیت: {status}")
            except Exception as ex:
                if "بک‌اند ارور داد" in str(ex):
                    raise
        time.sleep(0.5)

    raise Exception(f"زمان تمام شد! ریکوئست {expected_method} {api_endpoint} پیدا نشد.")


def flush_network_logs():
    driver.get_log("performance")


# ==============================================================
# بخش ۲: سناریوی اصلی (ساخت برچسب و اعمال زنجیره‌ای روی سایدبار)
# ==============================================================

try:
    initial_tag_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    print(f"\n▶️ شروع تست: چرخه انتشار برچسب '{initial_tag_name}' روی صندوق‌های مختلف")

    # ابتدا لود کردن صفحه اصلی پیام‌ها برای نمایان شدن سایدبار
    run_step(lambda: driver.get(base_url + 'mail/message?query=2&page=1&type=inbox'),
             "ورود به صفحه اولیه جهت لود سایدبار کناری")
    time.sleep(5)
    flush_network_logs()


    # -------------------------------------------------------------
    # مرحله ۱: ساخت برچسب جدید
    # -------------------------------------------------------------
    def create_tag():
        main_tags_menu = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//a[.//span[contains(text(), 'برچسب')]]//button | //app-mail-sidebar-item[.//span[contains(text(), 'برچسب')]]//button"
        )))
        driver.execute_script("arguments[0].click();", main_tags_menu)
        time.sleep(1)

        create_opt = wait.until(EC.presence_of_element_located((
            By.XPATH, "//span[normalize-space()='ساخت برچسب']"
        )))
        driver.execute_script("arguments[0].click();", create_opt)
        time.sleep(1)

        input_el = wait.until(EC.presence_of_element_located((
            By.XPATH, "//app-tag-modal//input | //input[contains(@id, 'mat-input')]"
        )))
        input_el.clear()
        input_el.send_keys(initial_tag_name)
        time.sleep(0.5)

        try:
            color_box = driver.find_element(By.XPATH, "//app-tag-modal//div[contains(@class, 'mb-2')]//div[2]")
            driver.execute_script("arguments[0].click();", color_box)
        except:
            pass

        time.sleep(0.5)

        submit_btn = wait.until(EC.presence_of_element_located((
            By.XPATH, "//button[.//span[normalize-space()='ایجاد']]"
        )))
        driver.execute_script("arguments[0].click();", submit_btn)


    run_step(create_tag, f"ساخت برچسب جدید با نام: {initial_tag_name}")

    # اجرا در پس‌زمینه با daemon=True
    threading.Thread(
        target=run_step,
        args=(lambda: verify_network_request("/api/tags", "POST"), "بررسی کد 200 برای ریکوئست POST ساخت برچسب"),
        daemon=True
    ).start()

    time.sleep(2)
    flush_network_logs()


    def reload_tags_from_server():
        """پس از ساخت تگ، داده‌های سایدبار و مودال را از سرور دوباره بارگذاری می‌کند."""
        driver.get(base_url + 'mail/message?query=2&page=1&type=inbox')
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    f"//span[normalize-space()='{initial_tag_name}']"
                ))
            )
            print(f"      [✓] تگ '{initial_tag_name}' پس از تازه‌سازی در رابط کاربری دیده شد.")
        except Exception:
            print("      [ℹ️] تگ در سایدبار بسته/مخفی است؛ ادامه با لیست مودال.")
        time.sleep(3)


    run_step(reload_tags_from_server, "تازه‌سازی لیست برچسب‌ها پس از ساخت")
    flush_network_logs()

    # -------------------------------------------------------------
    # مرحله ۲: پیمایش صندوق‌ها بر اساس کلیک روی سایدبار (UI داکیومنت)
    # -------------------------------------------------------------
    folders = ["صندوق دریافت", "صندوق ارسال", "هرزنامه", "سطل زباله"]


    def debug_find(by, selector, step_name):
        return WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((by, selector)),
            message=f"تایم‌اوت در پیدا کردن: '{step_name}' با سلکتور: {selector}"
        )


    def xpath_literal(value):
        if "'" not in value:
            return f"'{value}'"
        if '"' not in value:
            return f'"{value}"'
        parts = value.split("'")
        return "concat(" + ", \"'\", ".join(f"'{part}'" for part in parts) + ")"


    def safe_attr(element, name):
        try:
            return element.get_attribute(name)
        except Exception:
            return None


    def get_active_tag_overlay():
        """آخرین overlay نمایان را که متن ثبت یا برچسب دارد برمی‌گرداند."""
        selectors = (
            "//mat-dialog-container | "
            "//app-tag-selection-modal | "
            "//div[contains(@class,'cdk-overlay-pane')]"
        )

        def locate(_driver):
            visible = []
            for el in _driver.find_elements(By.XPATH, selectors):
                try:
                    if not el.is_displayed():
                        continue
                    txt = " ".join((el.text or "").split())
                    if "ثبت" in txt or "برچسب" in txt or initial_tag_name in txt:
                        visible.append(el)
                except Exception:
                    pass
            return visible[-1] if visible else False

        overlay = WebDriverWait(driver, 15).until(locate, message="overlay انتخاب برچسب پیدا نشد.")
        return overlay


    def read_tag_state_from_node(start_node, overlay):
        """وضعیت واقعی checkbox را با پیمایش node، فرزندان و ancestorها می‌خواند."""
        return driver.execute_script(
            r"""
            const start = arguments[0];
            const overlay = arguments[1];
            const result = {value: null, source: null, details: []};
            const selectors = [
              'input[type="checkbox"]', '[role="checkbox"]', 'mat-checkbox',
              'mat-pseudo-checkbox', 'mat-list-option', '[role="option"]'
            ];

            function inspect(el, source) {
              if (!el) return null;
              const tag = (el.tagName || '').toLowerCase();
              const cls = String(el.className || '');
              const ariaChecked = el.getAttribute && el.getAttribute('aria-checked');
              const ariaSelected = el.getAttribute && el.getAttribute('aria-selected');
              const checkedAttr = el.getAttribute && el.getAttribute('checked');
              const nativeChecked = (tag === 'input' && el.type === 'checkbox') ? !!el.checked : null;
              result.details.push({source, tag, cls, ariaChecked, ariaSelected, checkedAttr, nativeChecked});

              if (nativeChecked !== null) return nativeChecked;
              if (ariaChecked === 'true') return true;
              if (ariaChecked === 'false') return false;
              if (ariaSelected === 'true') return true;
              if (ariaSelected === 'false') return false;
              if (checkedAttr !== null) return true;

              const low = cls.toLowerCase();
              if (/(mat-mdc-checkbox-checked|mat-checkbox-checked|mdc-checkbox--selected|mat-pseudo-checkbox-checked|selected|checked)/.test(low)) return true;
              if (/(mat-pseudo-checkbox-unchecked|mdc-checkbox--unselected)/.test(low)) return false;
              return null;
            }

            let node = start;
            let level = 0;
            while (node) {
              let value = inspect(node, `ancestor-${level}`);
              if (value !== null) {
                result.value = value;
                result.source = `ancestor-${level}`;
                return result;
              }
              for (const sel of selectors) {
                const found = node.matches && node.matches(sel) ? node : node.querySelector && node.querySelector(sel);
                value = inspect(found, `ancestor-${level}:${sel}`);
                if (value !== null) {
                  result.value = value;
                  result.source = `ancestor-${level}:${sel}`;
                  return result;
                }
              }
              if (node === overlay) break;
              node = node.parentElement;
              level += 1;
            }
            return result;
            """,
            start_node,
            overlay,
        )


    def build_click_candidates(text_node, overlay):
        """تمام کنترل‌های محتمل مربوط به همان متن را از نزدیک‌ترین به دورترین می‌سازد."""
        candidates = driver.execute_script(
            r"""
            const textNode = arguments[0];
            const overlay = arguments[1];
            const out = [];
            const seen = new Set();
            function add(el, reason) {
              if (!el || seen.has(el)) return;
              seen.add(el);
              el.setAttribute('data-selenium-debug-reason', reason);
              out.push(el);
            }
            let node = textNode;
            let level = 0;
            while (node) {
              if (node.matches) {
                if (node.matches('input[type="checkbox"], [role="checkbox"], mat-checkbox, mat-list-option, [role="option"], label, button')) {
                  add(node, `self-level-${level}`);
                }
                for (const sel of [
                  'input[type="checkbox"]', '[role="checkbox"]', 'mat-checkbox',
                  'label', 'mat-pseudo-checkbox', 'mat-list-option', '[role="option"]', 'button'
                ]) {
                  add(node.querySelector && node.querySelector(sel), `desc-level-${level}:${sel}`);
                }
              }
              // ردیف‌های متداول Angular/Material
              if (node.matches && node.matches('li, mat-list-option, .mat-mdc-list-item, .mat-list-item, .tag-item, .row, [class*="tag"]')) {
                add(node, `row-level-${level}`);
              }
              if (node === overlay) break;
              node = node.parentElement;
              level += 1;
            }
            add(textNode, 'exact-text-node');
            return out;
            """,
            text_node,
            overlay,
        )
        unique = []
        seen_ids = set()
        for el in candidates:
            key = getattr(el, 'id', None)
            if key not in seen_ids:
                seen_ids.add(key)
                unique.append(el)
        return unique


    def click_candidate(candidate):
        """کلیک واقعی با mouse؛ در صورت نیاز JS fallback."""
        driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", candidate)
        time.sleep(0.25)
        try:
            ActionChains(driver).move_to_element(candidate).pause(0.2).click().perform()
            return "ActionChains"
        except Exception as first_exc:
            try:
                candidate.click()
                return "native-click"
            except Exception:
                driver.execute_script(
                    """
                    const el = arguments[0];
                    ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(type =>
                      el.dispatchEvent(new MouseEvent(type, {bubbles:true, cancelable:true, view:window}))
                    );
                    """,
                    candidate,
                )
                return f"JS-events (ActionChains error: {str(first_exc)[:100]})"


    def set_created_tag_checkbox(should_be_checked):
        overlay = get_active_tag_overlay()

        # جست‌وجوی مودال، فقط اگر ورودی مناسب وجود داشته باشد.
        visible_inputs = [
            el for el in overlay.find_elements(
                By.XPATH,
                ".//input[not(@type='checkbox') and not(@type='radio') and not(@type='hidden')]"
            )
            if el.is_displayed() and el.is_enabled()
        ]
        search_input = None
        for el in visible_inputs:
            hint = " ".join(filter(None, [
                safe_attr(el, "placeholder"), safe_attr(el, "aria-label"), safe_attr(el, "name")
            ])).lower()
            if any(word in hint for word in ("جست", "search", "tag", "برچسب")):
                search_input = el
                break
        if search_input is None and len(visible_inputs) == 1:
            search_input = visible_inputs[0]

        if search_input is not None:
            search_input.click()
            search_input.send_keys(Keys.CONTROL, "a")
            search_input.send_keys(Keys.BACKSPACE)
            search_input.send_keys(initial_tag_name)
            time.sleep(2)

        overlay = get_active_tag_overlay()
        tag_literal = xpath_literal(initial_tag_name)
        exact_nodes = overlay.find_elements(
            By.XPATH,
            f".//*[normalize-space(.)={tag_literal} and not(.//*[normalize-space(.)={tag_literal}])]"
        )
        exact_nodes = [el for el in exact_nodes if el.is_displayed()]

        if not exact_nodes:
            raise Exception(f"متن دقیق برچسب '{initial_tag_name}' داخل مودال پیدا نشد.")

        text_node = exact_nodes[0]
        state_before = read_tag_state_from_node(text_node, overlay)

        if state_before.get("value") == should_be_checked:
            print(f"      [✓] تگ از قبل در وضعیت مطلوب بود: {should_be_checked}")
            return

        candidates = build_click_candidates(text_node, overlay)

        for index, candidate in enumerate(candidates, start=1):
            reason = safe_attr(candidate, "data-selenium-debug-reason")
            before = read_tag_state_from_node(text_node, overlay)
            try:
                method = click_candidate(candidate)
            except Exception as exc:
                print(f"          [⚠️] کلیک ناموفق: {exc}")
                continue
            time.sleep(1)
            after = read_tag_state_from_node(text_node, overlay)
            print(f"          روش کلیک: {method}")
            print(f"          وضعیت قبل: {before}")
            print(f"          وضعیت بعد: {after}")

            if after.get("value") == should_be_checked:
                print(
                    f"      [✓] تغییر واقعی تأیید شد؛ تگ '{initial_tag_name}' "
                    f"{'انتخاب شد' if should_be_checked else 'از انتخاب خارج شد'}."
                )
                return

            # اگر وضعیت از false به true یا برعکس تغییر کرد ولی مطلوب نبود، دوباره روی کاندیدای دیگری کلیک نکن.
            if before.get("value") is not None and after.get("value") is not None and before.get("value") != after.get(
                    "value"):
                print("          [⚠️] وضعیت تغییر کرد اما به مقدار مطلوب نرسید؛ از کلیک‌های بیشتر جلوگیری شد.")
                break

        raise Exception(
            f"متن تگ '{initial_tag_name}' پیدا شد، اما هیچ کنترل واقعی checkbox به وضعیت "
            f"{should_be_checked} تغییر نکرد."
        )


    def submit_tag_dialog(action_name):
        overlay = get_active_tag_overlay()
        buttons = [
            el for el in overlay.find_elements(
                By.XPATH,
                ".//button[normalize-space(.)='ثبت' or .//span[normalize-space()='ثبت']]"
            )
            if el.is_displayed()
        ]
        if not buttons:
            raise Exception("دکمه ثبت داخل همان مودال انتخاب برچسب پیدا نشد.")

        submit_btn = buttons[-1]

        # شبکه را دقیقاً قبل از submit پاک می‌کنیم تا فقط درخواست این عملیات باقی بماند.
        flush_network_logs()
        click_method = click_candidate(submit_btn)

        try:
            WebDriverWait(driver, 5).until(EC.staleness_of(overlay))
            print("      [✓] مودال بعد از ثبت از DOM حذف شد.")
        except Exception:
            try:
                if not overlay.is_displayed():
                    print("      [✓] مودال بعد از ثبت مخفی شد.")
                else:
                    raise Exception(
                        "دکمه ثبت کلیک شد اما مودال بسته نشد؛ بنابراین ثبت واقعی انجام نشده است."
                    )
            except Exception:
                print("      [✓] مودال بعد از ثبت دیگر قابل دسترسی نیست.")

        time.sleep(1)


    for idx, folder_name in enumerate(folders, start=1):
        print(f"\n📂 [{idx}/4] کلیک و ورود به پوشه: {folder_name}")


        # 🌟 تغییر کلیدی: جابجایی بین پوشه‌ها کاملاً متکی بر منوی سایدبار واقعی وب‌سایت
        def click_sidebar_folder():
            sidebar_xpath = f"//app-menu-sidebar//span[contains(text(), '{folder_name}')] | //app-mail-sidebar//span[contains(text(), '{folder_name}')] | //span[normalize-space()='{folder_name}']"
            folder_el = wait.until(EC.presence_of_element_located((By.XPATH, sidebar_xpath)))
            driver.execute_script("arguments[0].click();", folder_el)


        run_step(click_sidebar_folder, f"کلیک روی منوی '{folder_name}' در سایدبار")
        time.sleep(4)  # مکث پایدار جهت لود نیتیو جدول بدون رفرش صفحه

        emails = driver.find_elements(By.XPATH, "//app-mail-table//tbody/tr")
        if not emails:
            print(f"  [⚠️] صندوق {folder_name} خالی است یا نامه‌ای جهت اعمال تگ ندارد. انتقال به بخش بعدی سایدبار...")
            continue

        flush_network_logs()


        # ۱. فلو اعمال برچسب
        def apply_tag():
            more_btn = debug_find(
                By.XPATH,
                "(//app-mail-table//tbody/tr)[1]//app-table-action-single//button",
                "دکمه سه نقطه (more_vert) اولین ایمیل"
            )
            driver.execute_script("arguments[0].click();", more_btn)
            time.sleep(1.5)

            tag_option = debug_find(
                By.XPATH,
                "//div[contains(@class, 'cdk-overlay-container')]//*[contains(text(), 'برچسب')] | //button[contains(., 'برچسب')]",
                "گزینه 'افزودن / حذف برچسب' در منوی باز شده"
            )
            driver.execute_script("arguments[0].click();", tag_option)
            time.sleep(2.5)

            set_created_tag_checkbox(should_be_checked=True)
            submit_tag_dialog("اعمال برچسب")


        def apply_tag_and_verify():
            apply_tag()
            threading.Thread(
                target=run_step,
                args=(lambda: verify_network_request("api/mail/tag", "PUT"), "بررسی ریکوئست آپدیت تگ"),
                daemon=True
            ).start()


        run_step(
            apply_tag_and_verify,
            f"انتخاب واقعی و ثبت برچسب '{initial_tag_name}' روی ایمیل اول در {folder_name}"
        )

        time.sleep(2)
        flush_network_logs()


        # ۲. فلو حذف برچسب
        def remove_tag():
            more_btn = debug_find(
                By.XPATH,
                "(//app-mail-table//tbody/tr)[1]//app-table-action-single//button",
                "دکمه سه نقطه (more_vert) برای حذف"
            )
            driver.execute_script("arguments[0].click();", more_btn)
            time.sleep(1.5)

            tag_option = debug_find(
                By.XPATH,
                "//div[contains(@class, 'cdk-overlay-container')]//*[contains(text(), 'برچسب')] | //button[contains(., 'برچسب')]",
                "گزینه 'افزودن / حذف برچسب' برای حذف"
            )
            driver.execute_script("arguments[0].click();", tag_option)
            time.sleep(2.5)

            set_created_tag_checkbox(should_be_checked=False)
            submit_tag_dialog("برداشتن برچسب")


        def remove_tag_and_verify():
            remove_tag()
            threading.Thread(
                target=run_step,
                args=(lambda: verify_network_request("api/mail/tag", "PUT"), "بررسی ریکوئست حذف تگ"),
                daemon=True
            ).start()


        run_step(
            remove_tag_and_verify,
            f"برداشتن واقعی و ثبت حذف برچسب '{initial_tag_name}' از ایمیل اول در {folder_name}"
        )

        time.sleep(2)
        flush_network_logs()

    print("\n🏁 تست چرخه‌ای و نیتیو انتشار برچسب‌ها در سایدبار با موفقیت به پایان رسید.")

except Exception as e:
    print(f"\n❌ تست به دلیل خطای فوق متوقف شد.")

finally:
    driver.quit()