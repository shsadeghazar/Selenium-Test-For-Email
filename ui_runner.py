import tkinter as tk
from tkinter import ttk, messagebox
import json
import subprocess
import threading
import os
import jdatetime  # 🌟 اضافه شدن کتابخانه تاریخ شمسی

# لیست اسکریپت‌های تست شما
TEST_SCRIPTS = {
    "لاگین و ذخیره سشن": "login_and_save.py",
    "ارسال ایمیل ساده": "test_send_email.py",
    "ارسال ایمیل با پیوست": "test_send_with_attachment.py",
    "ریپلای به اولین ایمیل": "test_reply_email.py",
    "ساخت پوشه و پوشه تکراری": "test_create_folder.py"
}

# ساخت پوشه برای ذخیره لاگ‌های مجزا
os.makedirs("logs", exist_ok=True)


def open_log_file(file_path):
    """باز کردن فایل لاگ (HTML) در مرورگر سیستم"""
    try:
        os.startfile(os.path.abspath(file_path))
    except Exception as e:
        messagebox.showerror("خطا", f"امکان باز کردن فایل لاگ وجود ندارد:\n{e}")


def save_config_and_run():
    url = url_entry.get().strip()
    user = user_entry.get().strip()
    password = pass_entry.get().strip()
    target_email = email_entry.get().strip()

    # 🌟 دریافت مقادیر CC و BCC
    cc_email = cc_entry.get().strip()
    bcc_email = bcc_entry.get().strip()

    # 🌟 دریافت تاریخ از دیت‌پیکر
    selected_date = f"{year_var.get()}-{month_var.get()}-{day_var.get()}"
    current_time_for_file = jdatetime.datetime.now().strftime("%H-%M-%S")
    timestamp_for_name = f"{selected_date}_{current_time_for_file}"

    # 🌟 بررسی فیلدهای اجباری (CC و BCC اجباری نیستند)
    if not url or not user or not password or not target_email:
        messagebox.showwarning("خطا", "لطفاً تمام فیلدهای الزامی اطلاعات سامانه را پر کنید.")
        return

    # ۱. ذخیره اطلاعات در فایل کانفیگ
    config_data = {
        "url": url,
        "username": user,
        "password": password,
        "target_email": target_email,
        "cc_email": cc_email,  # 🌟 ذخیره CC در کانفیگ
        "bcc_email": bcc_email,  # 🌟 ذخیره BCC در کانفیگ
        "run_date": selected_date
    }
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)

    # استخراج تست‌های انتخاب شده
    selected_tests = [(name, TEST_SCRIPTS[name]) for name, var in test_vars.items() if var.get()]

    if not selected_tests:
        messagebox.showwarning("خطا", "لطفاً حداقل یک سناریو را برای اجرا انتخاب کنید.")
        return

    # تغییر وضعیت UI هنگام شروع
    run_btn.config(state=tk.DISABLED)
    log_text.insert(tk.END, "🚀 شروع اجرای تست‌ها...\n" + "=" * 50 + "\n", "normal")
    log_text.see(tk.END)

    for name, _ in selected_tests:
        status_labels[name].config(text="⏳ در صف اجرا...", foreground="orange")
        log_buttons[name].config(state=tk.DISABLED)

    # ۲. اجرای تست‌ها در Thread جداگانه
    def execute_tests():
        for name, script in selected_tests:
            status_labels[name].config(text="🔄 در حال اجرا...", foreground="blue")

            # 🌟 نمایش تاریخ در متن لاگ (ترمینال زنده)
            log_text.insert(tk.END, f"\n▶️ اجرای سناریو: {name}\n📅 تاریخ اجرا: {selected_date}\n", "normal")
            log_text.see(tk.END)

            # 🌟 اضافه شدن تاریخ و زمان دقیق به اسم فایل لاگ برای جلوگیری از تداخل
            log_file_path = os.path.join("logs", f"{script.replace('.py', '')}_{timestamp_for_name}_log.html")

            success_steps = 0
            error_steps = 0

            try:
                # ساختار پایه فایل HTML
                with open(log_file_path, "w", encoding="utf-8") as log_file:
                    log_file.write(
                        '<html><body style="background-color:#1e1e1e; color:#ffffff; font-family:Tahoma, Consolas; direction:rtl; padding:20px;">')
                    log_file.write(f'<h3 style="color:#00ff00;">📄 لاگ اجرای سناریو: {name}</h3>')
                    # 🌟 نوشتن تاریخ در هدر فایل لاگ دانلودی
                    log_file.write(
                        f'<h4 style="color:#aaaaaa;">📅 تاریخ ثبت شده: {selected_date} | زمان: {jdatetime.datetime.now().strftime("%H:%M:%S")}</h4>')
                    log_file.write(
                        '<pre style="font-family:Consolas, monospace; font-size:14px; white-space:pre-wrap;">\n')

                    # اجرای اسکریپت
                    process = subprocess.Popen(['python', script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                               text=True, encoding='utf-8')

                    # خواندن زنده لاگ‌ها و اعمال رنگ‌ها
                    for line in process.stdout:
                        clean_line = line.strip()

                        # 🌟 اصلاح منطق: فقط چک کردن آیکون‌ها، کلمات "خطا" یا "Error" بررسی نمی‌شوند!
                        if "[✓]" in clean_line or "✅" in clean_line or "[🛡️]" in clean_line:
                            success_steps += 1
                            ui_tag = "success"
                            html_line = f'<span style="color:#00ff00;">{clean_line}</span>\n'
                        elif "[⚠️]" in clean_line or "❌" in clean_line:
                            error_steps += 1
                            ui_tag = "error"
                            html_line = f'<span style="color:#ff3333;">{clean_line}</span>\n'
                        elif "[ℹ️]" in clean_line:
                            # این موارد باگ نیستند، فقط پیام اطلاعاتی هستند و درصد را خراب نمی‌کنند
                            ui_tag = "info"
                            html_line = f'<span style="color:#34dbeb;">{clean_line}</span>\n'
                        else:
                            ui_tag = "normal"
                            html_line = f'<span style="color:#cccccc;">{clean_line}</span>\n'

                        log_text.insert(tk.END, line, ui_tag)
                        log_text.see(tk.END)

                        log_file.write(html_line)

                    process.wait()

                    # محاسبه درصد موفقیت
                    total_steps = success_steps + error_steps
                    if total_steps > 0:
                        percentage = int((success_steps / total_steps) * 100)
                    else:
                        percentage = 100 if process.returncode == 0 else 0

                    if percentage == 100:
                        status_labels[name].config(text=f"✅ موفق ({percentage}٪)", foreground="green")
                    elif percentage > 0:
                        status_labels[name].config(text=f"⚠️ ناقص ({percentage}٪)", foreground="#d35400")
                    else:
                        status_labels[name].config(text=f"❌ شکست ({percentage}٪)", foreground="red")

                    log_file.write('</pre></body></html>')

            except Exception as e:
                error_msg = f"❌ خطای سیستمی: {str(e)}\n"
                log_text.insert(tk.END, error_msg, "error")
                status_labels[name].config(text="❌ خطای سیستمی (۰٪)", foreground="red")
                with open(log_file_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f'<span style="color:#ff3333;">{error_msg}</span></pre></body></html>')

            # روشن کردن دکمه لاگ
            log_buttons[name].config(state=tk.NORMAL, command=lambda p=log_file_path: open_log_file(p))

        log_text.insert(tk.END, "\n" + "=" * 50 + "\n🏁 تمام سناریوهای انتخابی به پایان رسید.\n", "success")
        log_text.see(tk.END)
        run_btn.config(state=tk.NORMAL)

    threading.Thread(target=execute_tests, daemon=True).start()


# --- طراحی UI پیشرفته ---
root = tk.Tk()
root.title("Selenium Automation Runner - Pro Edition")
root.geometry("650x850")  # 🌟 ارتفاع بیشتر شد تا فیلدهای CC و BCC جا بشوند
root.configure(padx=20, pady=15)

style = ttk.Style()
style.theme_use('clam')
style.configure("TButton", font=("Tahoma", 9, "bold"), padding=5)
style.configure("TLabelframe.Label", font=("Tahoma", 10, "bold"), foreground="#333333")

# --- بخش ورودی اطلاعات ---
frame_inputs = ttk.LabelFrame(root, text=" ⚙️ تنظیمات و اطلاعات سامانه ", padding=15)
frame_inputs.pack(fill="x", pady=10)

ttk.Label(frame_inputs, text="لینک سامانه:", font=("Tahoma", 9)).grid(row=0, column=0, sticky="w", pady=5)
url_entry = ttk.Entry(frame_inputs, width=55)
url_entry.grid(row=0, column=1, pady=5, padx=10)
url_entry.insert(0, "https://mail.chbeta.ir/nui/")

ttk.Label(frame_inputs, text="نام کاربری:", font=("Tahoma", 9)).grid(row=1, column=0, sticky="w", pady=5)
user_entry = ttk.Entry(frame_inputs, width=55)
user_entry.grid(row=1, column=1, pady=5, padx=10)

ttk.Label(frame_inputs, text="رمز عبور:", font=("Tahoma", 9)).grid(row=2, column=0, sticky="w", pady=5)
pass_entry = ttk.Entry(frame_inputs, width=55, show="*")
pass_entry.grid(row=2, column=1, pady=5, padx=10)

# 🌟 فیلدهای ایمیل
ttk.Label(frame_inputs, text="گیرنده (To) - جدا با کاما:", font=("Tahoma", 9)).grid(row=3, column=0, sticky="w", pady=5)
email_entry = ttk.Entry(frame_inputs, width=55)
email_entry.grid(row=3, column=1, pady=5, padx=10)
email_entry.insert(0, "shayan2@chbeta.ir")

ttk.Label(frame_inputs, text="رونوشت (CC) - اختیاری:", font=("Tahoma", 9)).grid(row=4, column=0, sticky="w", pady=5)
cc_entry = ttk.Entry(frame_inputs, width=55)
cc_entry.grid(row=4, column=1, pady=5, padx=10)

ttk.Label(frame_inputs, text="رونوشت پنهان (BCC) - اختیاری:", font=("Tahoma", 9)).grid(row=5, column=0, sticky="w",
                                                                                       pady=5)
bcc_entry = ttk.Entry(frame_inputs, width=55)
bcc_entry.grid(row=5, column=1, pady=5, padx=10)

# 🌟 بخش دیت‌پیکر شمسی
ttk.Label(frame_inputs, text="تاریخ اجرا (شمسی):", font=("Tahoma", 9)).grid(row=6, column=0, sticky="w", pady=5)

date_frame = ttk.Frame(frame_inputs)
date_frame.grid(row=6, column=1, sticky="w", pady=5, padx=10)

now = jdatetime.datetime.now()

# روز
day_var = tk.StringVar(value=f"{now.day:02d}")
day_cb = ttk.Combobox(date_frame, textvariable=day_var, values=[f"{i:02d}" for i in range(1, 32)], width=3,
                      state="readonly")
day_cb.pack(side="right", padx=2)
ttk.Label(date_frame, text="/", font=("Tahoma", 9)).pack(side="right")

# ماه
month_var = tk.StringVar(value=f"{now.month:02d}")
month_cb = ttk.Combobox(date_frame, textvariable=month_var, values=[f"{i:02d}" for i in range(1, 13)], width=3,
                        state="readonly")
month_cb.pack(side="right", padx=2)
ttk.Label(date_frame, text="/", font=("Tahoma", 9)).pack(side="right")

# سال
year_var = tk.StringVar(value=str(now.year))
year_cb = ttk.Combobox(date_frame, textvariable=year_var, values=[str(i) for i in range(1402, 1415)], width=5,
                       state="readonly")
year_cb.pack(side="right", padx=2)

# --- بخش سناریوهای اسکرول‌دار ---
frame_tests = ttk.LabelFrame(root, text=" 📋 انتخاب و وضعیت سناریوها ", padding=10)
frame_tests.pack(fill="both", expand=True, pady=10)

canvas = tk.Canvas(frame_tests, highlightthickness=0)
scrollbar = ttk.Scrollbar(frame_tests, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

test_vars = {}
status_labels = {}
log_buttons = {}

for i, (name, script) in enumerate(TEST_SCRIPTS.items()):
    var = tk.BooleanVar(value=True)
    test_vars[name] = var

    chk = ttk.Checkbutton(scrollable_frame, text=name, variable=var, width=30)
    chk.grid(row=i, column=0, sticky="w", pady=5, padx=5)

    lbl_status = ttk.Label(scrollable_frame, text="آماده اجرا", font=("Tahoma", 9, "bold"), width=15, foreground="gray")
    lbl_status.grid(row=i, column=1, sticky="w", pady=5, padx=10)
    status_labels[name] = lbl_status

    btn_log = ttk.Button(scrollable_frame, text="📄 مشاهده لاگ", width=12, state=tk.DISABLED)
    btn_log.grid(row=i, column=2, sticky="e", pady=5, padx=5)
    log_buttons[name] = btn_log

run_btn = ttk.Button(root, text="🚀 شــروع اجــرای تسـت‌هــا", command=save_config_and_run)
run_btn.pack(pady=10, fill="x", ipady=5)

# --- بخش لاگ زنده ---
ttk.Label(root, text="ترمینال زنده:", font=("Tahoma", 9, "bold")).pack(anchor="w")

log_text = tk.Text(root, height=12, bg="#1e1e1e", font=("Consolas", 10), padx=10, pady=10)
log_text.tag_config("success", foreground="#00ff00")
log_text.tag_config("error", foreground="#ff3333")
log_text.tag_config("info", foreground="#34dbeb")  # 🌟 اضافه شدن رنگ فیروزه‌ای برای [ℹ️]
log_text.tag_config("normal", foreground="#ffffff")
log_text.pack(fill="both", expand=True)

root.mainloop()
