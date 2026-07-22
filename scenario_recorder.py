import time
import json
import os
import sys
import select
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ==============================================================
# بخش ۱: خواندن کانفیگ، تنظیم مرورگر و تزریق سشن اولیه
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

print("\n🚀 اسکریپت ضبط فوق‌پیشرفته (Full-Stack Angular, DOM & Network Interceptor) اجرا شد.")

# ورود اولیه جهت تزریق سشن
driver.get(base_url + "robots.txt")
time.sleep(1.5)

if os.path.exists("session.json"):
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
        print(f"⚠️ خطا در تزریق سشن: {e}")

driver.get(base_url + "mail/message?query=2&page=1&type=inbox")
time.sleep(2)

# ==============================================================
# بخش ۲: تزریق موتور شنودگر قدرتمند JavaScript
# ==============================================================

JS_INTERCEPTOR = """
if (!window.__full_recorder_injected__) {
    window.__full_recorder_injected__ = true;
    window.__recorded_scenario__ = { steps: [], api_calls: [] };

    // -------------------------------------------------------------
    // ۱. پایش و ثبت کامل درخواست‌های شبکه (Fetch & XHR API)
    // -------------------------------------------------------------
    const origFetch = window.fetch;
    window.fetch = async function(...args) {
        let url = typeof args[0] === 'string' ? args[0] : (args[0] ? args[0].url : '');
        let options = args[1] || {};
        let method = options.method || 'GET';
        let body = options.body || null;

        const response = await origFetch.apply(this, args);
        const clone = response.clone();
        let resBody = null;
        try { resBody = await clone.json(); } catch(e) {}

        if (url && url.includes('/api/')) {
            window.__recorded_scenario__.api_calls.push({
                type: 'FETCH',
                url: url,
                method: method,
                payload: body,
                status: response.status,
                response: resBody,
                time: new Date().toLocaleTimeString()
            });
        }
        return response;
    };

    const origXHRXSend = window.XMLHttpRequest.prototype.send;
    const origXHROpen = window.XMLHttpRequest.prototype.open;
    window.XMLHttpRequest.prototype.open = function(method, url) {
        this._url = url;
        this._method = method;
        return origXHROpen.apply(this, arguments);
    };
    window.XMLHttpRequest.prototype.send = function(body) {
        this.addEventListener('load', function() {
            if (this._url && this._url.includes('/api/')) {
                let resBody = null;
                try { resBody = JSON.parse(this.responseText); } catch(e) {}
                window.__recorded_scenario__.api_calls.push({
                    type: 'XHR',
                    url: this._url,
                    method: this._method,
                    payload: body,
                    status: this.status,
                    response: resBody,
                    time: new Date().toLocaleTimeString()
                });
            }
        });
        return origXHRXSend.apply(this, arguments);
    };

    // -------------------------------------------------------------
    // ۲. توابع کمکی جراحی عناصر DOM و آنگولار
    // -------------------------------------------------------------
    function getFullXPath(el) {
        if (!el || el.nodeType !== 1) return '';
        if (el.id) return '//*[@id="' + el.id + '"]';
        if (el === document.body) return '//body';
        let ix = 0;
        let siblings = el.parentNode ? el.parentNode.childNodes : [];
        for (let i = 0; i < siblings.length; i++) {
            let sib = siblings[i];
            if (sib === el) return getFullXPath(el.parentNode) + '/' + el.tagName.toLowerCase() + '[' + (ix + 1) + ']';
            if (sib.nodeType === 1 && sib.tagName === el.tagName) ix++;
        }
        return '';
    }

    function getSmartXPath(el) {
        if (!el) return '';
        let tag = el.tagName.toLowerCase();
        let text = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
        if (text && text.length > 0 && text.length < 40 && !text.includes('\\n')) {
            return "//" + tag + "[normalize-space()='" + text + "'] | //*[normalize-space()='" + text + "']";
        }
        let attrs = ['placeholder', 'aria-label', 'formcontrolname', 'title', 'name', 'id'];
        for (let a of attrs) {
            let val = el.getAttribute(a);
            if (val) return "//" + tag + "[@" + a + "='" + val + "']";
        }
        return getFullXPath(el);
    }

    function getAngularAttributes(el) {
        let attrs = {};
        for (let attr of el.attributes) {
            if (attr.name.startsWith('ng-') || attr.name.startsWith('mat-') || attr.name.startsWith('aria-') || 
                ['id', 'class', 'placeholder', 'formcontrolname', 'type', 'role'].includes(attr.name)) {
                attrs[attr.name] = attr.value;
            }
        }
        return attrs;
    }

    function getParentHierarchy(el) {
        let parents = [];
        let curr = el.parentElement;
        let depth = 0;
        while (curr && depth < 8) {
            parents.push({
                tag: curr.tagName.toLowerCase(),
                id: curr.id || null,
                class: curr.className || null,
                isOverlay: curr.classList.contains('cdk-overlay-container') || curr.classList.contains('cdk-overlay-pane'),
                isDialog: curr.tagName.toLowerCase().includes('dialog') || curr.tagName.toLowerCase().includes('modal')
            });
            curr = curr.parentElement;
            depth++;
        }
        return parents;
    }

    // -------------------------------------------------------------
    // ۳. شنود رویدادهای کاربر (Click, Input, KeyDown)
    // -------------------------------------------------------------
    document.addEventListener('click', function(e) {
        let el = e.target;
        let clickable = el.closest('button, a, input, select, [role="button"], mat-option, tr, li, mat-tree-node') || el;
        window.__recorded_scenario__.steps.push({
            time: new Date().toLocaleTimeString(),
            type: 'CLICK',
            tag: clickable.tagName.toLowerCase(),
            text: (clickable.innerText || clickable.textContent || '').trim().replace(/\\s+/g, ' ').substring(0, 100),
            id: clickable.id || null,
            className: clickable.className || null,
            smart_xpath: getSmartXPath(clickable),
            full_xpath: getFullXPath(clickable),
            angular_attrs: getAngularAttributes(clickable),
            parents: getParentHierarchy(clickable),
            active_element: document.activeElement ? document.activeElement.tagName.toLowerCase() : null
        });
    }, true);

    document.addEventListener('input', function(e) {
        let el = e.target;
        if (['input', 'textarea', 'select'].includes(el.tagName.toLowerCase())) {
            window.__recorded_scenario__.steps.push({
                time: new Date().toLocaleTimeString(),
                type: 'INPUT_CHANGE',
                tag: el.tagName.toLowerCase(),
                value: el.value,
                id: el.id || null,
                className: el.className || null,
                smart_xpath: getSmartXPath(el),
                full_xpath: getFullXPath(el),
                angular_attrs: getAngularAttributes(el),
                parents: getParentHierarchy(el)
            });
        }
    }, true);
}
"""


def inject_recorder():
    try:
        driver.execute_script(JS_INTERCEPTOR)
    except Exception:
        pass


inject_recorder()

print("\n" + "=" * 75)
print("🔴 موتور ضبط همه‌فن‌حریف فعال شد!")
print("👉 به مرورگر بروید و سناریو را کامل اجرا کنید (ساخت پوشه، انتقال، زیرپوشه و...)")
print("⚡ تمام داده‌ها به‌صورت لحظه‌ای در فایل 'recorded_scenario.json' ذخیره می‌شوند.")
print("👉 برای پایان ضبط می‌توانید دکمه 'Ctrl + C' را در همین ترمینال بزنید.")
print("=" * 75 + "\n")

# ==============================================================
# بخش ۳: حلقه پایش زنده و ذخیره‌سازی لحظه‌ای (Real-time Flush)
# ==============================================================

master_data = {"steps": [], "api_calls": []}

try:
    while True:
        time.sleep(1)

        # ۱. اطمینان از تزریق بودن شنودگر (در صورت ریلود شدن صفحه)
        inject_recorder()

        # ۲. استخراج داده‌های جدید از مرورگر
        try:
            fetched_data = driver.execute_script("""
                if (window.__recorded_scenario__) {
                    let d = JSON.parse(JSON.stringify(window.__recorded_scenario__));
                    window.__recorded_scenario__ = { steps: [], api_calls: [] };
                    return d;
                }
                return { steps: [], api_calls: [] };
            """)

            new_steps = fetched_data.get("steps", [])
            new_apis = fetched_data.get("api_calls", [])

            if new_steps or new_apis:
                master_data["steps"].extend(new_steps)
                master_data["api_calls"].extend(new_apis)

                for st in new_steps:
                    print(
                        f"🖱️ [UI {st['type']}] <{st['tag']}> | متن: '{st.get('text', '')}' | Smart XPath: {st['smart_xpath']}")
                for api in new_apis:
                    print(f"🌐 [API {api['method']}] Status: {api['status']} | URL: {api['url']}")

                # 🌟 ذخیره لحظه‌ای در فایل JSON (حتی اگر اسکریپت ناگهانی قطع شود)
                with open("recorded_scenario.json", "w", encoding="utf-8") as f:
                    json.dump(master_data, f, ensure_ascii=False, indent=4)

        except Exception:
            # مرورگر ممکن است بسته‌شده باشد یا صفحه در حال لود باشد
            pass

except KeyboardInterrupt:
    print("\n\n⏹️ ضبط سناریو با دستور کاربر (Ctrl + C) متوقف شد.")

finally:
    # ذخیره نهایی
    with open("recorded_scenario.json", "w", encoding="utf-8") as f:
        json.dump(master_data, f, ensure_ascii=False, indent=4)

    print("\n" + "=" * 75)
    print(f"✅ فایل ذخیره‌سازی جامع با موفقیت ساخته شد: 'recorded_scenario.json'")
    print(f"📊 مجموع اکشن‌های ثبت‌شده: {len(master_data['steps'])}")
    print(f"🌐 مجموع درخواست‌های API ثبت‌شده: {len(master_data['api_calls'])}")
    print("=" * 75)

    try:
        driver.quit()
    except Exception:
        pass