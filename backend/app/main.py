"""
MemeVault API - BLUEPRINT uyumlu Modular Monolith giriş noktası.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlangıç/bitiş (DB pool, vb.)."""
    # Örnek kullanıcı yoksa oluştur (veritabanı sıfırlandığında giriş yapılabilmesi için)
    try:
        from app.seed_user import seed_default_user
        seed_default_user()
        print("[MemeVault] Örnek hesap hazır: deneme@gmail.com / deneme")
    except Exception as e:
        print(f"[MemeVault] Örnek hesap oluşturulamadı (Docker/DB çalışıyor mu?): {e}")
    
    # S3 bucket yoksa oluştur (MinIO ilk çalıştırmada bucket yoktur)
    try:
        from app.services.storage import ensure_bucket_exists
        ensure_bucket_exists()
        print("[MemeVault] S3 bucket hazır")
    except Exception as e:
        print(f"[MemeVault] S3 bucket kontrolü başarısız (MinIO çalışıyor mu?): {e}")
    
    yield
    # shutdown: cleanup


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS - Frontend için gerekli
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health():
    """Sağlık kontrolü."""
    return {"status": "ok"}
