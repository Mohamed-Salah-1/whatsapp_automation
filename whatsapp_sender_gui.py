import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import csv
import io
import time
import os
import sys
import urllib.parse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ---------- core logic ----------

def parse_csv(text: str) -> list[tuple[str, str]]:
    recipients = []
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if not row:
            continue
        parts = [p.strip() for p in row]
        if len(parts) < 2:
            continue
        phone_raw, name = parts[0], parts[1]
        phone_raw = phone_raw.replace("+", "").strip()
        if not phone_raw or not phone_raw.isdigit():
            continue
        recipients.append(("+" + phone_raw, name.strip()))
    return recipients


def build_text(name: str, body: str) -> str:
    name = (name or "").strip()
    greeting = f"السلام عليكم {name}" if name else "السلام عليكم"
    return f"{greeting}\n{body}"


USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".whatsapp_session")
os.makedirs(USER_DATA_DIR, exist_ok=True)


def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(900, 700)
    return driver


def send_whatsapp(driver, phone: str, text: str, log_callback, timeout=45):
    encoded = urllib.parse.quote(text)
    url = f"https://web.whatsapp.com/send?phone={phone[1:]}&text={encoded}"
    log_callback(f"  Loading WhatsApp Web for {phone}...")
    driver.get(url)

    wait = WebDriverWait(driver, timeout)

    # wait for either the send button or the message input to appear
    send_xpath = "//button[@aria-label='Send' or @aria-label='إرسال']"
    try:
        send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, send_xpath)))
        send_btn.click()
        log_callback(f"  Clicked send button.")
    except Exception:
        msg_xpath = "//div[@contenteditable='true']"
        msg_box = wait.until(EC.presence_of_element_located((By.XPATH, msg_xpath)))
        msg_box.send_keys(Keys.ENTER)
        log_callback(f"  Pressed Enter to send.")

    time.sleep(2)


# ---------- GUI ----------

class WhatsAppSenderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.driver = None
        root.title("WhatsApp Bulk Sender")
        root.geometry("750+{}+{}".format(
            (root.winfo_screenwidth() - 750) // 2,
            (root.winfo_screenheight() - 750) // 2
        ))
        root.minsize(600, 650)

        # ---- recipients ----
        tk.Label(root, text="Recipients (phone,name — one per line, no header)",
                 anchor="w").pack(fill="x", padx=10, pady=(10, 0))
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=10, pady=(2, 0))
        tk.Button(btn_frame, text="📁 Load CSV file", command=self.load_csv).pack(side="left")
        tk.Button(btn_frame, text="📋 Paste from clipboard", command=self.paste_clipboard).pack(side="left", padx=5)

        self.csv_text = scrolledtext.ScrolledText(root, height=8, font=("Consolas", 10))
        self.csv_text.pack(fill="x", padx=10, pady=(2, 5))

        # ---- message ----
        tk.Label(root, text="Message body:", anchor="w").pack(fill="x", padx=10, pady=(5, 0))
        self.msg_text = scrolledtext.ScrolledText(root, height=14, font=("Consolas", 10))
        self.msg_text.pack(fill="x", padx=10, pady=(2, 5))
        self._load_default_message()

        # ---- status & send ----
        status_frame = tk.Frame(root)
        status_frame.pack(fill="x", padx=10, pady=(0, 5))
        self.status_label = tk.Label(status_frame, text="Ready", fg="gray")
        self.status_label.pack(side="left")
        self.send_btn = tk.Button(status_frame, text="🚀 Send All", font=("", 12, "bold"),
                                  bg="#25D366", fg="white", padx=20,
                                  command=self.start_send)
        self.send_btn.pack(side="right")

        # ---- log ----
        tk.Label(root, text="Log:", anchor="w").pack(fill="x", padx=10)
        self.log_text = scrolledtext.ScrolledText(root, height=8, font=("Consolas", 9),
                                                  state="disabled", bg="#1a1a1a", fg="#00ff00")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ---- helpers ----

    def _load_default_message(self):
        default = """السلام عليكم {name}
يسعد شركة نجمة الحدود للخدمات اللوجستية التواصل معكم، ونود دعوتكم لحضور مقابلة عمل غدًا في مقر الشركة بمدينة الدمام من الساعة التاسعة صباحا الى الساعة الرابعة مساء.

الوظيفة: مندوب توصيل طلبات
المزايا: سيارة – بنزين – شريحة مكالمات وإنترنت
الدخل: رواتب مجزية مع حوافز مجدية عند تحقيق الأهداف الشهرية

طبيعة العمل: تشمل توصيل الطلبات عبر تطبيقات التوصيل المختلفة وفق آلية عمل واضحة وأهداف شهرية محددة.

أيام العمل: 6 أيام أسبوعيًا
الإجازة: يوم واحد أسبوعيًا

نرجو تأكيد حضوركم، ونتطلع لرؤيتكم في الموعد المحدد.
موقع المكتب
https://maps.app.goo.gl/qZvYcnyRkjRb6Ekp7?g_st=awb
الدور الثاني , مكتب رقم 216"""
        self.msg_text.insert("1.0", default)

    def log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.root.update()

    def set_status(self, text: str, color: str = "gray"):
        self.status_label.configure(text=text, fg=color)
        self.root.update()

    def load_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
            self.csv_text.delete("1.0", "end")
            self.csv_text.insert("1.0", content)
            self.log(f"Loaded {len(parse_csv(content))} recipients from {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file:\n{e}")

    def paste_clipboard(self):
        try:
            text = self.root.clipboard_get()
        except Exception:
            messagebox.showinfo("Clipboard", "Could not read clipboard.")
            return
        self.csv_text.delete("1.0", "end")
        self.csv_text.insert("1.0", text)

    def get_recipients(self) -> list[tuple[str, str]]:
        raw = self.csv_text.get("1.0", "end-1c").strip()
        if not raw:
            raise ValueError("No recipients entered.")
        recipients = parse_csv(raw)
        if not recipients:
            raise ValueError("No valid recipients found. Format: phone,name")
        return recipients

    # ---- send logic ----

    def start_send(self):
        try:
            recipients = self.get_recipients()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self.send_btn.configure(state="disabled", text="⏳ Sending...")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        thread = threading.Thread(target=self._send_all, args=(recipients,), daemon=True)
        thread.start()

    def _send_all(self, recipients: list[tuple[str, str]]):
        body = self.msg_text.get("1.0", "end-1c").strip()
        total = len(recipients)

        self.log("🚀 Opening Chrome...")
        self.set_status("Opening Chrome...", "#1a73e8")

        try:
            self.driver = create_driver()
            self.log("Chrome opened successfully.")
            self.log("⏳ If QR code appears, scan it with your phone (you only need to do this once).")

            for i, (phone, name) in enumerate(recipients, 1):
                text = build_text(name, body)
                self.set_status(f"📤 ({i}/{total}) Sending to {name}...", "#1a73e8")
                self.log(f"[{i}/{total}] Sending to {phone} ({name})...")
                send_whatsapp(self.driver, phone, text, self.log)
                self.log(f"✅ Sent to {phone} ({name})")

            self.set_status(f"✅ Done! {total} messages sent.", "green")
            self.log(f"\n🎉 All {total} messages sent successfully!")
            messagebox.showinfo("Complete", f"All {total} messages sent!")

        except Exception as e:
            self.log(f"❌ Error: {e}")
            self.set_status("❌ Failed — check log", "red")
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.send_btn.configure(state="normal", text="🚀 Send All")


# ---------- entry ----------

def main():
    root = tk.Tk()
    app = WhatsAppSenderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
