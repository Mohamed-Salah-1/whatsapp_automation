import pywhatkit
import time
import os


def load_recipients_from_csv(csv_path: str):
    """CSV format: first column = number (no +), second column = name."""
    recipients = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            # allow both comma and semicolon separators
            # Expected: phone,name
            parts = [p.strip() for p in line.replace(";", ",").split(",")]
            if len(parts) < 2:
                # fallback: sometimes values are separated by whitespace
                parts_ws = line.split()
                if len(parts_ws) < 2:
                    continue
                phone_raw, name = parts_ws[0], " ".join(parts_ws[1:])
            else:
                phone_raw, name = parts[0], parts[1]

            phone_raw = phone_raw.replace("+", "").strip()
            # accept numbers-only (after removing +)
            if not phone_raw or not phone_raw.isdigit():
                continue

            recipients.append(("+" + phone_raw, name.strip()))

    return recipients



def build_message(name: str, message_body: str) -> str:
    name = (name or "").strip()
    if name:
        return f"السلام عليكم {name}\n{message_body}"
    return f"السلام عليكم\n{message_body}"


def main():
    try:
        csv_path = "./recipients.csv"  # you can rename if you want
        message_body = """
        يسعد شركة نجمة الحدود للخدمات اللوجستية التواصل معكم، ونود دعوتكم لحضور مقابلة عمل غدًا في مقر الشركة بمدينة الدمام من الساعة التاسعة صباحا الى الساعة الرابعة مساء.

الوظيفة: مندوب توصيل طلبات
المزايا: سيارة – بنزين – شريحة مكالمات وإنترنت
الدخل: رواتب مجزية مع حوافز مجدية عند تحقيق الأه

داف الشهرية

طبيعة العمل: تشمل توصيل الطلبات عبر تطبيقات التوصيل المختلفة وفق آلية عمل واضحة وأهداف شهرية محددة.

أيام العمل: 6 أيام أسبوعيًا
الإجازة: يوم واحد أسبوعيًا

نرجو تأكيد حضوركم، ونتطلع لرؤيتكم في الموعد المحدد.
موقع المكتب
https://maps.app.goo.gl/qZvYcnyRkjRb6Ekp7?g_st=awb
الدور الثاني , مكتب رقم 216
        
        """
        

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV not found: {os.path.abspath(csv_path)}")

        recipients = load_recipients_from_csv(csv_path)
        if not recipients:
            raise ValueError("No valid recipients found in CSV")

        for phone, name in recipients:
            text = build_message(name, message_body)
            pywhatkit.sendwhatmsg_instantly(phone, text, tab_close=True)
            print(f"Message sent to {phone} ({name})")
            time.sleep(2)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()

