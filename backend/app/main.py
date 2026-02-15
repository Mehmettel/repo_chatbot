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
    except Exception as e:
        print(f"[Startup] Seed user atlandı: {e}")
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
