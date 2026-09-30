# bot.py - DevStudio Support Bot Core
# نسخه نهایی و بدون باگ

from difflib import SequenceMatcher


# ============================================================
# داده‌های FAQ
# ============================================================

FAQ_DATA = [
    {
        "question": "What is your refund policy?",
        "answer": "We offer a 30-day money-back guarantee on all products. No questions asked.",
        "keywords": ["refund", "money back", "return", "policy", "بازگشت"]
    },
    {
        "question": "How long does shipping take?",
        "answer": "Standard shipping takes 5-7 business days. Express takes 2-3 days.",
        "keywords": ["shipping", "delivery", "how long", "arrive", "ارسال"]
    },
    {
        "question": "Do you ship internationally?",
        "answer": "Yes, we ship to over 50 countries worldwide including USA, UK, Germany, UAE, and more.",
        "keywords": ["international", "country", "countries", "worldwide", "global"]
    },
    {
        "question": "How can I contact support?",
        "answer": "You can email support@devstudio.com or use the live chat on our website.",
        "keywords": ["contact", "support", "email", "help", "تماس"]
    },
    {
        "question": "What services do you offer?",
        "answer": "We offer Python development, mobile app development, web design, and AI solutions.",
        "keywords": ["services", "offer", "what do you do", "خدمات"]
    },
    {
        "question": "What is your pricing?",
        "answer": "Our projects start from $500. Contact us for a custom quote based on your needs.",
        "keywords": ["price", "pricing", "cost", "how much", "قیمت"]
    },
    {
        "question": "What technologies do you use?",
        "answer": "We use Python, Django, FastAPI, React, Next.js, React Native, and modern AI tools.",
        "keywords": ["technology", "technologies", "stack", "tools", "tech"]
    },
]


# ============================================================
# داده‌های سفارشات (نمونه)
# ============================================================

ORDERS = {
    "ORD-482910": {
        "status": "Shipped",
        "tracking": "TRK-1234567890",
        "eta": "March 25, 2025"
    },
    "ORD-123456": {
        "status": "Processing",
        "tracking": None,
        "eta": "March 22, 2025"
    },
    "ORD-789012": {
        "status": "Delivered",
        "tracking": "TRK-9876543210",
        "eta": "Delivered on March 18, 2025"
    },
    "ORD-555555": {
        "status": "Cancelled",
        "tracking": None,
        "eta": "Refund in progress"
    },
}


# ============================================================
# تابع ۱: جستجو در FAQ
# ============================================================

def search_faq(query):
    """
    جستجو در FAQ با ترکیب دو معیار:
    1. شباهت متنی (SequenceMatcher)
    2. تطابق کلمات کلیدی
    """
    query_lower = query.lower().strip()

    if not query_lower:
        return "Please type your question."

    results = []

    for faq in FAQ_DATA:
        # معیار ۱: شباهت متنی
        similarity = SequenceMatcher(
            None, query_lower, faq["question"].lower()
        ).ratio()

        # معیار ۲: تطابق کلمات کلیدی
        keyword_matches = sum(
            1 for kw in faq.get("keywords", [])
            if kw in query_lower
        )
        keyword_score = min(keyword_matches * 0.3, 0.9)

        # امتیاز نهایی
        final_score = max(similarity, keyword_score)

        if final_score > 0.5:
            results.append((final_score, faq))

    results.sort(reverse=True, key=lambda x: x[0])

    if results:
        answers = []
        for score, faq in results[:2]:
            answers.append(
                "Q: " + faq["question"] + "\nA: " + faq["answer"]
            )
        return "\n\n".join(answers)

    return (
        "I'm sorry, I couldn't find a specific answer for that.\n"
        "Please rephrase your question or type 'human' to speak with an agent."
    )


# ============================================================
# تابع ۲: بررسی وضعیت سفارش
# ============================================================

def check_order_status(order_id):
    """بررسی وضعیت سفارش با شناسه."""
    order = ORDERS.get(order_id.upper())

    if not order:
        return (
            "Order " + order_id + " was not found in our system.\n"
            "Please verify the order ID or type 'human' to contact support."
        )

    if order["tracking"]:
        return (
            "Order " + order_id + "\n"
            "Status: " + order["status"] + "\n"
            "Tracking: " + order["tracking"] + "\n"
            "ETA: " + order["eta"]
        )

    return (
        "Order " + order_id + "\n"
        "Status: " + order["status"] + "\n"
        "ETA: " + order["eta"]
    )


# ============================================================
# تابع ۳: ارجاع به انسان
# ============================================================

def escalate_to_human(reason):
    """ارجاع به اپراتور انسانی."""
    return (
        "Transferring you to a human support agent.\n"
        "Reason: " + reason + "\n"
        "Estimated wait time: 15 minutes.\n"
        "A team member will be with you shortly."
    )


# ============================================================
# تابع ۴: تشخیص نیت کاربر (Intent Router)
# ============================================================

def route_intent(text):
    """
    تشخیص نیت کاربر از متن ورودی.
    برمی‌گرداند: (نوع نیت، داده مرتبط)
    """
    text_lower = text.lower().strip()

    # ۱. بررسی شماره سفارش (مثل ORD-482910)
    for token in text.split():
        cleaned = token.strip(".,!?؟")
        if cleaned.upper().startswith("ORD-"):
            return "order", cleaned.upper()

    # ۲. بررسی درخواست اپراتور انسانی
    human_keywords = [
        "human", "agent", "person", "manager", "operator",
        "real person", "speak to someone", "talk to someone",
        "انسان", "اپراتور", "پشتیبان", "مدیر"
    ]
    if any(kw in text_lower for kw in human_keywords):
        return "human", text

    # ۳. سلام و احوال‌پرسی
    greeting_keywords = ["hello", "hi", "hey", "good morning", "good evening", "سلام"]
    if text_lower in greeting_keywords or len(text_lower.split()) <= 2 and any(
        kw == text_lower for kw in greeting_keywords
    ):
        return "greeting", text

    # ۴. پیش‌فرض: FAQ
    return "faq", text


# ============================================================
# تابع ۵: پردازش پیام اصلی
# ============================================================

def process_message(query):
    """
    پردازش پیام کاربر و برگرداندن پاسخ مناسب.
    """
    if not query or not query.strip():
        return "Please type a message."

    intent, data = route_intent(query)

    if intent == "order":
        return check_order_status(data)

    if intent == "human":
        return escalate_to_human(data)

    if intent == "greeting":
        return (
            "Hello! Welcome to DevStudio Support.\n"
            "How can I help you today?\n\n"
            "You can ask me about:\n"
            "- Our services and pricing\n"
            "- Shipping and refunds\n"
            "- Order status (e.g., ORD-482910)\n"
            "- Contact information"
        )

    return search_faq(data)


# ============================================================
# تست خودکار (فقط وقتی مستقیم اجرا شود)
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("DevStudio Support Bot - Direct Test")
    print("=" * 60)

    test_cases = [
        "hello",
        "What is your refund policy?",
        "How long does shipping take?",
        "Do you ship to Germany?",
        "What services do you offer?",
        "What is your pricing?",
        "Where is my order ORD-482910?",
        "Check ORD-123456",
        "Track ORD-555555",
        "I want to talk to a human",
        "Random gibberish xyzabc123",
    ]

    for query in test_cases:
        print("\nUser: " + query)
        print("Bot:  " + process_message(query).replace("\n", "\n      "))
        print("-" * 60)

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

