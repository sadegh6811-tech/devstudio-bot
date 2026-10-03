#!/usr/bin/env python3
import json
import re
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse


FAQ_DATA = [
    {"q_fa": "سیاست بازگشت کالا چیست؟", "a_fa": "۳۰ روز ضمانت بازگشت وجه داریم.", "q_en": "What is your refund policy?", "a_en": "30-day money-back guarantee.", "kw_fa": ["بازگشت", "وجه", "پول"], "kw_en": ["refund", "return"]},
    {"q_fa": "چه خدماتی ارائه می‌دهید؟", "a_fa": "پایتون، اپلیکیشن موبایل، طراحی وب و هوش مصنوعی.", "q_en": "What services do you offer?", "a_en": "Python, mobile apps, web design, and AI.", "kw_fa": ["خدمات", "ارائه"], "kw_en": ["services", "offer"]},
    {"q_fa": "قیمت‌ها چگونه است؟", "a_fa": "پروژه‌ها از ۵۰۰ دلار شروع می‌شوند.", "q_en": "What is your pricing?", "a_en": "Projects start from $500.", "kw_fa": ["قیمت", "هزینه"], "kw_en": ["price", "cost"]},
]

ORDERS = {
    "ORD-482910": {"s_fa": "ارسال شده", "s_en": "Shipped", "t": "TRK-1234567890"},
    "ORD-123456": {"s_fa": "در حال پردازش", "s_en": "Processing", "t": None},
}


def detect_lang(text):
    if not text:
        return "en"
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
        kw_score = min(kw_match * 0.4, 1.0)
        score = max(overlap, kw_score)
        if score > 0.4:
            results.append((score, item))
    results.sort(reverse=True, key=lambda x: x[0])
    if results:
        parts = []
        for _, item in results[:2]:
            if lang == "fa":
                parts.append("س: " + item["q_fa"] + "\nج: " + item["a_fa"])
            else:
                parts.append("Q: " + item["q_en"] + "\nA: " + item["a_en"])
        return "\n\n".join(parts)
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


def escalate(reason, lang):
    if lang == "fa":
        return "شما به اپراتور انسانی متصل می‌شوید."
    return "Transferring to a human agent."


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
        return escalate(query, lang)
    
    if any(k in tl for k in ["thanks", "ممنون", "سپاس"]):
        return "خواهش می‌کنم!" if lang == "fa" else "You're welcome!"
    
    if any(k in tl for k in ["bye", "خداحافظ"]):
        return "خداحافظ!" if lang == "fa" else "Goodbye!"
    
    if len(words) <= 4 and any(k in tl for k in ["hello", "hi", "سلام", "درود"]):
        return "سلام! 👋 به DevStudio خوش آمدید." if lang == "fa" else "Hello! 👋 Welcome to DevStudio."
    
    faq = search_faq(query, lang)
    if faq:
        return faq
    
    if lang == "fa":
        return "متأسفم، پاسخ مناسبی پیدا نکردم. لطفاً سوالتان را بازنویسی کنید."
    return "Sorry, no answer found."


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
                "service": "DevStudio Bot v2.1",
                "cors": "enabled"
            }))
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
    print("DevStudio Bot v2.1 - Port: " + str(port))
    print("=" * 50)
    try:
        HTTPServer(("0.0.0.0", port), H).serve_forever()
    except KeyboardInterrupt:
        print("Stopped")
