import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import csv
import io
import time
import os
import sys


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


def auto_send(phone: str, text: str):
    import pywhatkit
    pywhatkit.sendwhatmsg_instantly(phone, text, tab_close=True, wait_time=15)


# ---------- GUI ----------

class WhatsAppSenderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("WhatsApp Bulk Sender")
        root.geometry("750x750")
        root.minsize(600, 600)

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
            import pywhatkit  # noqa: F401
        except ImportError:
            messagebox.showerror(
                "Missing dependency",
                "pywhatkit is not installed.\n\n"
                "Run this in a terminal:\n  pip install pywhatkit\n\n"
                "Then restart the app."
            )
            return

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

        try:
            for i, (phone, name) in enumerate(recipients, 1):
                text = build_text(name, body)
                self.set_status(f"📤 ({i}/{total}) Sending to {name}...", "#1a73e8")
                self.log(f"[{i}/{total}] Sending to {phone} ({name})...")
                auto_send(phone, text)
                self.log(f"✅ Sent to {phone} ({name})")
                time.sleep(3)
        except Exception as e:
            self.log(f"❌ Error: {e}")
            self.set_status("❌ Failed — check log", "red")
            self.send_btn.configure(state="normal", text="🚀 Send All")
            return

        self.set_status(f"✅ Done! {total} messages sent.", "green")
        self.log(f"\n🎉 All {total} messages sent successfully!")
        self.send_btn.configure(state="normal", text="🚀 Send All")
        messagebox.showinfo("Complete", f"All {total} messages sent!")


# ---------- entry ----------

def main():
    root = tk.Tk()
    app = WhatsAppSenderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
