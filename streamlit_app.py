import streamlit as st
import pandas as pd
import urllib.parse
import csv
import io
import textwrap

st.set_page_config(page_title="WhatsApp Bulk Sender", page_icon="💬", layout="centered")

# ---------- helpers ----------

def parse_csv(file_or_text) -> list[tuple[str, str]]:
    recipients = []
    if file_or_text is None:
        return recipients
    if hasattr(file_or_text, "getvalue"):
        raw = file_or_text.getvalue()
        content = raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw
    else:
        content = file_or_text
    reader = csv.reader(io.StringIO(content))
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


def build_wa_link(phone: str, message: str) -> str:
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{phone[1:]}?text={encoded}"


def build_text(name: str, body: str) -> str:
    name = (name or "").strip()
    greeting = f"السلام عليكم {name}" if name else "السلام عليكم"
    return f"{greeting}\n{body}"


def generate_script(recipients: list[tuple[str, str]], body: str) -> str:
    recipients_literal = repr(recipients)
    body_literal = repr(body)
    return textwrap.dedent(f'''\
    import pywhatkit
    import time

    recipients = {recipients_literal}

    message_body = {body_literal}

    def build_text(name: str, body: str) -> str:
        name = (name or "").strip()
        greeting = f"السلام عليكم {{name}}" if name else "السلام عليكم"
        return f"{{greeting}}\\n{{body}}"

    for phone, name in recipients:
        text = build_text(name, message_body)
        print(f"Sending to {{phone}} ({{name}})...")
        pywhatkit.sendwhatmsg_instantly(phone, text, tab_close=True, wait_time=15)
        print(f"Sent to {{phone}} ({{name}})")
        time.sleep(3)

    print("Done! All messages sent.")
    ''')


# ---------- session state ----------
if "log" not in st.session_state:
    st.session_state.log = []


# ---------- sidebar ----------
mode = st.sidebar.radio(
    "Mode",
    ["🔗 Generate wa.me links", "📥 Download auto-send script"],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Instructions")
st.sidebar.markdown(
    "- CSV format: **phone,name** (no header, no `+`)\n"
    "- One recipient per line\n"
    "- Phone numbers must be full international (e.g. `966537148588`)"
)

st.sidebar.markdown("### 📥 Script mode")
st.sidebar.markdown(
    "1. Configure recipients + message below\n"
    "2. Click **Download script**\n"
    "3. Save the `.py` file on your computer\n"
    "4. Run: `pip install pywhatkit && python send_whatsapp.py`\n"
    "5. Make sure WhatsApp Web is logged in on Chrome"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🪟 Windows app (no Python needed)")
st.sidebar.markdown(
    "There's also a standalone `.exe` version in this repo:\n"
    "**`whatsapp_sender_gui.py`** — a desktop app with a simple GUI.\n\n"
    "To build it:\n"
    "1. `pip install pyinstaller pywhatkit`\n"
    "2. Run `build_exe.bat`\n"
    "3. Share `dist/WhatsApp_Sender.exe` with your friend"
)


# ---------- main ----------
st.title("💬 WhatsApp Bulk Sender")
st.markdown("Upload a CSV or paste recipients, write your message.")

# --- Recipients input ---
tab_csv, tab_paste = st.tabs(["📁 Upload CSV", "✏️ Paste manually"])

recipients: list[tuple[str, str]] = []

with tab_csv:
    uploaded = st.file_uploader("Choose a CSV file", type=["csv", "txt"])
    if uploaded is not None:
        recipients = parse_csv(uploaded)

with tab_paste:
    raw = st.text_area("Paste CSV content (one per line: phone,name)", height=150)
    if raw:
        recipients = parse_csv(io.StringIO(raw))

if recipients:
    df = pd.DataFrame(recipients, columns=["Phone", "Name"])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"**{len(recipients)}** recipient(s) loaded")
else:
    st.info("Load recipients to get started.")

# --- Message ---
st.markdown("---")
st.subheader("📝 Message")

default_body = """يسعد شركة نجمة الحدود للخدمات اللوجستية التواصل معكم، ونود دعوتكم لحضور مقابلة عمل غدًا في مقر الشركة بمدينة الدمام من الساعة التاسعة صباحا الى الساعة الرابعة مساء.

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

message_body = st.text_area("Message body", value=default_body, height=300, key="message_body")

st.markdown("### Preview (first recipient)")
if recipients and message_body:
    preview_name = recipients[0][1]
    preview_text = build_text(preview_name, message_body)
    st.code(preview_text, language="text", line_numbers=True)

# --- Action ---
st.markdown("---")

if not recipients or not message_body.strip():
    st.warning("Add recipients and a message first.")
    st.stop()

if mode == "🔗 Generate wa.me links":
    if st.button("🔗 Generate WhatsApp Links", type="primary", use_container_width=True):
        st.session_state.log = []
        links_text = ""
        for phone, name in recipients:
            text = build_text(name, message_body.strip())
            link = build_wa_link(phone, text)
            st.session_state.log.append(f"✅ {phone} ({name})")
            links_text += f"{link}\n"

        st.success(f"Generated {len(recipients)} links")
        for phone, name in recipients:
            link = build_wa_link(phone, build_text(name, message_body.strip()))
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{name}** — {phone}")
            with col2:
                st.markdown(f"[📱 Open]({link})", unsafe_allow_html=True)

        st.text_area("Copy all links (paste in browser tab to open multiple)", links_text, height=100)
        st.info("Click each link or copy them all — WhatsApp Web opens with the message pre-filled. Just press Enter to send.")

else:  # download script
    script_content = generate_script(recipients, message_body.strip())

    st.download_button(
        label="📥 Download auto-send script",
        data=script_content,
        file_name="send_whatsapp.py",
        mime="text/x-python",
        type="primary",
        use_container_width=True,
    )

    with st.expander("📄 Preview the script"):
        st.code(script_content, language="python")
