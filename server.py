from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuthRequest(BaseModel):
    email: str = ""
    password: str
    username: str | None = None

@app.get("/api/health")
def health(): return {"status": "ok"}

@app.post("/api/auth/register")
def register(req: AuthRequest):
    return {"success": True, "token": "mock_token_123", "message": "User registered"}

@app.post("/api/auth/login")
def login(req: AuthRequest):
    return {"success": True, "token": "mock_token_123", "message": "Logged in"}
