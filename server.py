#!/usr/bin/env python3
import json
import re
import os
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
SUPPORT_EMAIL = "sadegh6811@gmail.com"
SUPPORT_PHONE = "+989189376811"

FAQ_DATA = [
    {"q_fa": "سیاست بازگشت کالا چیست", "a_fa": "۳۰ روز ضمانت بازگشت وجه بدون سوال داریم.", "q_en": "What is your refund policy", "a_en": "30-day money-back guarantee.", "kw_fa": ["بازگشت", "وجه", "مرجوع"], "kw_en": ["refund", "return"]},
    {"q_fa": "چه خدماتی ارائه می‌دهید", "a_fa": "برنامه‌نویسی پایتون، اپلیکیشن موبایل، طراحی وب و هوش مصنوعی.", "q_en": "What services do you offer", "a_en": "Python, mobile apps, web design, and AI solutions.", "kw_fa": ["خدمات", "ارائه"], "kw_en": ["services", "offer"]},
    {"q_fa": "قیمت‌ها چگونه است", "a_fa": "پروژه‌ها از ۵۰۰ دلار شروع می‌شوند.", "q_en": "What is your pricing", "a_en": "Projects start from $500.", "kw_fa": ["قیمت", "هزینه"], "kw_en": ["price", "cost"]},
    {"q_fa": "چگونه با پشتیبانی تماس بگیرم", "a_fa": "ایمیل: sadegh6811@gmail.com\nتلفن: +989189376811", "q_en": "How to contact support", "a_en": "Email: sadegh6811@gmail.com\nPhone: +989189376811", "kw_fa": ["تماس", "پشتیبانی", "شماره", "تلفن"], "kw_en": ["contact", "support", "phone"]},
]

ORDERS = {
    "ORD-482910": {"s_fa": "ارسال شده", "s_en": "Shipped", "t": "TRK-1234567890"},
    "ORD-123456": {"s_fa": "در حال پردازش", "s_en": "Processing", "t": None},
}

def detect_lang(text):
    if not text:
        return "en"
    # الفبای عربی مخصوص (حروفی که در فارسی نیستند)
    arabic_only = re.search(r'[\u0621\u0622\u0623\u0625\u0627\u0629\u062f\u0630\u0631\u0632\u0633\u0634\u0635\u0636\u0637\u0638\u0639\u063a\u0641\u0642\u0643\u0644\u0645\u0646\u0647\u0648\u064a\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669\u066a]', text)
    # اگر متن شامل کلمات خاص عربی باشد
    arabic_words = ["مرحبا", "كم", "تكلفة", "الموقع", "شكرا", "ما", "هل", "من", "ال", "على", "في", "كيف", "خدمات"]
    has_arabic_word = any(w in text for w in arabic_words)
    # اگر حروف فارسی خاص باشد → فارسی
    persian_specific = re.search(r'[\u067e\u0686\u0698\u06a9\u06af\u06cc]', text)
    if persian_specific:
        return "fa"
    if arabic_only or has_arabic_word:
        return "ar"
    if re.search(r'[\u0600-\u06FF]', text):
        return "fa"
    return "en"

def norm(s):
    s = s.lower().strip()
    s = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', s)
    return re.sub(r'\s+', ' ', s)

def get_oid(text):
    m = re.search(r'ORD[-\s]?(\d{4,})', text, re.IGNORECASE)
    return "ORD-" + m.group(1) if m else None

def search_faq(query, lang):
    q = norm(query)
    if not q:
        return None
    q_words = set(q.split())
    results = []
    for item in FAQ_DATA:
        if lang == "fa":
            target_q = norm(item["q_fa"])
            keywords = item["kw_fa"]
        else:
            target_q = norm(item["q_en"])
            keywords = item["kw_en"]
        target_words = set(target_q.split())
        overlap = len(q_words & target_words) / max(len(q_words), 1)
        kw_match = sum(1 for k in keywords if k in q)
        kw_score = min(kw_match * 0.5, 1.0)
        score = max(overlap, kw_score)
        if score > 0.7:
            results.append((score, item))
    results.sort(reverse=True, key=lambda x: x[0])
    if results:
        item = results[0][1]
        return item["a_fa"] if lang == "fa" else item["a_en"]
    return None

def check_order(oid, lang):
    order = ORDERS.get(oid.upper())
    if not order:
        return "سفارش " + oid + " پیدا نشد." if lang == "fa" else "Order " + oid + " not found."
    if lang == "fa":
        lines = ["سفارش " + oid, "وضعیت: " + order["s_fa"]]
        if order["t"]:
            lines.append("کد رهگیری: " + order["t"])
    else:
        lines = ["Order " + oid, "Status: " + order["s_en"]]
        if order["t"]:
            lines.append("Tracking: " + order["t"])
    return "\n".join(lines)

def ask_groq(message, lang):
    if not GROQ_API_KEY:
        return None
    system_prompt = (
        "You are DevStudio's support assistant. DevStudio is an international software agency.\n"
        "Services: Python, mobile apps, web design, AI. Pricing: from $500.\n"
        "Contact: sadegh6811@gmail.com | +989189376811\n\n"
        "CRITICAL: Reply in the EXACT same language as the user.\n"
        "- Persian text -> Persian reply\n"
        "- Arabic text -> Arabic reply\n"
        "- English text -> English reply\n"
        "Be concise (2-3 sentences). Be helpful."
    )
    try:
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "temperature": 0.5,
            "max_tokens": 400
        }
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + GROQ_API_KEY,
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("[Groq Error]", str(e))
        return None

def process(query):
    if not query or not query.strip():
        return "Please type a message."
    lang = detect_lang(query)
    tl = query.lower().strip()
    words = tl.split()
    oid = get_oid(query)
    if oid:
        return check_order(oid, lang)
    if any(k in tl for k in ["human", "agent", "انسان", "اپراتور"]):
        if lang == "fa":
            return "شما به اپراتور انسانی متصل می‌شوید.\nایمیل: sadegh6811@gmail.com\nتلفن: +989189376811"
        return "Transferring to a human agent.\nEmail: sadegh6811@gmail.com\nPhone: +989189376811"
    if any(k in tl for k in ["thanks", "ممنون", "سپاس", "مرسی"]):
        return "خواهش می‌کنم! سوال دیگری دارید؟" if lang == "fa" else "You're welcome!"
    if any(k in tl for k in ["bye", "خداحافظ"]):
        return "خداحافظ!" if lang == "fa" else "Goodbye!"
    pure_greeting_words = ["hello", "hi", "hey", "سلام", "درود", "صبح بخیر", "عصر بخیر"]
    if len(words) <= 2 and any(w in tl for w in pure_greeting_words):
        if lang == "fa":
            return "سلام! 👋 به DevStudio خوش آمدید. چطور می‌توانم کمکتان کنم؟"
        return "Hello! 👋 Welcome to DevStudio."
    faq = search_faq(query, lang)
    if faq:
        return faq
    groq_answer = ask_groq(query, lang)
    if groq_answer:
        return groq_answer
    if lang == "fa":
        return "متأسفم، پاسخ مناسبی پیدا نکردم.\nلطفاً تماس بگیرید: sadegh6811@gmail.com | +989189376811"
    return "Sorry, no answer found.\nContact us: sadegh6811@gmail.com | +989189376811"

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ["/", "/health", "/api/info"]:
            self._s(200, "application/json", json.dumps({
                "status": "healthy",
                "service": "DevStudio Bot v3.1",
                "cors": "enabled",
                "groq": "enabled" if GROQ_API_KEY else "disabled",
                "email": SUPPORT_EMAIL,
                "phone": SUPPORT_PHONE
            }, ensure_ascii=False))
        else:
            self._s(404, "text/plain", "Not Found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/chat":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                data = json.loads(body)
                message = data.get("message", "")
                reply = process(message)
                response = {
                    "reply": reply,
                    "lang": detect_lang(message),
                    "timestamp": datetime.now().isoformat()
                }
                self._s(200, "application/json", json.dumps(response, ensure_ascii=False))
            except Exception as e:
                self._s(500, "application/json", json.dumps({"error": str(e)}))
        else:
            self._s(404, "text/plain", "Not Found")

    def _s(self, code, ct, body):
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("=" * 50)
    print("DevStudio Bot v3.1 - Port: " + str(port))
    print("Groq: " + ("Enabled" if GROQ_API_KEY else "Disabled"))
    print("Email: " + SUPPORT_EMAIL)
    print("Phone: " + SUPPORT_PHONE)
    print("=" * 50)
    try:
        HTTPServer(("0.0.0.0", port), H).serve_forever()
    except KeyboardInterrupt:
        print("Stopped")
# v3.2 update Sun Oct  4 05:41:18 +0330 2026
