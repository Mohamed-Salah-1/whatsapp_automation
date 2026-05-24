import streamlit as st
import pandas as pd
import urllib.parse
import time
import os
import csv
import io

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


def auto_send(phone: str, text: str):
    import pywhatkit
    pywhatkit.sendwhatmsg_instantly(phone, text, tab_close=True, wait_time=10)


@st.dialog("⚠️ pywhatkit not installed")
def show_pywhatkit_dialog():
    st.write("`pywhatkit` is required for auto-send mode. Install it with:")
    st.code("pip install pywhatkit")
    if st.button("OK"):
        st.rerun()


# ---------- session state ----------
if "log" not in st.session_state:
    st.session_state.log = []


# ---------- sidebar ----------
mode = st.sidebar.radio(
    "Sending method",
    ["🔗 Generate wa.me links", "🤖 Auto-send via browser"],
    help="wa.me links work everywhere. Auto-send requires pywhatkit installed locally.",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Instructions")
st.sidebar.markdown(
    "- CSV format: **phone,name** (no header, no `+`)\n"
    "- One recipient per line\n"
    "- Phone numbers must be full international (e.g. `966537148588`)"
)


# ---------- main ----------
st.title("💬 WhatsApp Bulk Sender")
st.markdown("Upload a CSV or paste recipients, write your message, and send.")

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

col_reset, _ = st.columns([1, 5])
with col_reset:
    if st.button("↺ Reset to default", type="tertiary"):
        st.session_state.message_body = default_body
        st.rerun()

st.markdown("### Preview (first recipient)")
if recipients and message_body:
    preview_name = recipients[0][1]
    preview_text = build_text(preview_name, message_body)
    st.code(preview_text, language="text", line_numbers=True)

# --- Send / Generate ---
st.markdown("---")

if not recipients or not message_body.strip():
    st.warning("Add recipients and a message first.")
    st.stop()

if mode == "🔗 Generate wa.me links":
    if st.button("🔗 Generate WhatsApp Links", type="primary", use_container_width=True):
        st.session_state.log = []
        links = []
        for phone, name in recipients:
            text = build_text(name, message_body.strip())
            link = build_wa_link(phone, text)
            links.append((phone, name, link))
            st.session_state.log.append(f"✅ {phone} ({name})")

        st.success(f"Generated {len(links)} links")
        for phone, name, link in links:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{name}** — {phone}")
            with col2:
                st.markdown(f"[📱 Open WhatsApp]({link})", unsafe_allow_html=True)

        st.info("Click each link to open WhatsApp with the message pre-filled.")

else:  # auto-send mode
    try:
        import pywhatkit  # noqa: F401
        pywhatkit_available = True
    except ImportError:
        pywhatkit_available = False

    if not pywhatkit_available:
        show_pywhatkit_dialog()
        st.stop()

    if st.button("🚀 Send All Messages", type="primary", use_container_width=True):
        st.session_state.log = []
        progress = st.progress(0, text="Starting...")
        status = st.empty()

        for i, (phone, name) in enumerate(recipients):
            text = build_text(name, message_body.strip())
            try:
                status.info(f"📤 Sending to {name} ({phone})...")
                auto_send(phone, text)
                st.session_state.log.append(f"✅ {phone} ({name}) — sent")
                time.sleep(3)
            except Exception as e:
                st.session_state.log.append(f"❌ {phone} ({name}) — {e}")
            progress.progress((i + 1) / len(recipients), text=f"{i+1}/{len(recipients)}")

        status.success("✅ Done!")
        progress.empty()

    if st.session_state.log:
        st.markdown("### Log")
        for entry in st.session_state.log:
            st.text(entry)
