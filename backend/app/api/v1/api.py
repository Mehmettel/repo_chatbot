"""
API v1 router birleştirme - BLUEPRINT api/v1/api.py.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, folders, tags, videos

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(folders.router, prefix="/folders", tags=["folders"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
