import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
import os

app = FastAPI(title="Elen-t API", docs_url=None) # غیرفعال کردن docs پیش‌فرض برای سفارشی‌سازی

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>Elen-t</title></head>
        <body style="background:#0a0a0a;color:#fff;text-align:center;padding:50px;font-family:sans-serif;">
            <h1 style="color:#00e5ff;">پلتفرم Elen-t</h1>
            <p>سیستم کشف قوانین پنهان علم و سلامت</p>
            <a href="/docs" style="color:#00e5ff;text-decoration:none;border:1px solid #00e5ff;padding:10px 20px;border-radius:5px;">مشاهده مستندات API</a>
        </body>
    </html>
    """

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url=app.openapi_url, title="Elen-t API Docs")

@app.post("/api/auth/register")
def register():
    return {"status": "ok", "message": "ثبت‌نام با موفقیت انجام شد"}

@app.post("/api/auth/login")
def login():
    return {"status": "ok", "message": "ورود با موفقیت انجام شد"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
