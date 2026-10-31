from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
@app.get("/api/health")
def health(): return {"status": "ok"}

@app.post("/api/auth/register")
def register(): return {"status": "ok"}

@app.post("/api/auth/login")
def login(): return {"status": "ok"}
