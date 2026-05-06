import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Receipt Expense Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# uploads 디렉토리 자동 생성
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(exist_ok=True)

# 라우터 등록 (Phase 2~3에서 구현)
# from routers import upload, expenses, summary
# app.include_router(upload.router, prefix="/api")
# app.include_router(expenses.router, prefix="/api")
# app.include_router(summary.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Receipt Expense Tracker API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
