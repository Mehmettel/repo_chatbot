"""
Chatbot / Akıllı Arama - V2 Hybrid Search.
Semantik benzerlik + Full-text search birleşimi ile gelişmiş arama doğruluğu.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.db import get_db
from app.models import Folder, User
from app.services.intelligence.search import hybrid_search, keyword_boost_search

router = APIRouter()


class SearchQuery(BaseModel):
    q: str
    folder_id: UUID | None = None
    tag_ids: list[UUID] | None = None
    limit: int = 10
    search_mode: str = "hybrid"  # "hybrid", "keyword_boost", "vector"


class SearchResultItem(BaseModel):
    video_id: UUID
    s3_key: str | None
    title: str | None
    description_ai: str | None
    score: float
    vector_score: float | None = None
    fts_score: float | None = None


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    query: str
    search_mode: str


async def _user_folder_ids(db: AsyncSession, user_id: UUID) -> list[UUID]:
    result = await db.execute(select(Folder.id).where(Folder.user_id == user_id))
    return [r[0] for r in result.all()]


@router.post("/search", response_model=SearchResponse)
async def smart_search(
    payload: SearchQuery,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Akıllı Arama V2: Hybrid search (vektör + full-text) ile en alakalı videoları döner.
    
    search_mode:
    - "hybrid": Vektör + Full-text search birleşimi (varsayılan, önerilen)
    - "keyword_boost": Vektör search + keyword boost
    """
    folder_ids = await _user_folder_ids(db, user.id)
    
    if payload.search_mode == "keyword_boost":
        rows = await keyword_boost_search(
            db,
            query_text=payload.q,
            folder_ids=folder_ids,
            folder_id=payload.folder_id,
            limit=payload.limit,
            min_score=0.0,
        )
        results = [
            SearchResultItem(
                video_id=vid,
                s3_key=s3_key,
                title=title,
                description_ai=description_ai,
                score=round(score, 4),
            )
            for vid, s3_key, title, description_ai, score in rows
        ]
    else:
        # Default: hybrid search
        rows = await hybrid_search(
            db,
            query_text=payload.q,
            folder_ids=folder_ids,
            folder_id=payload.folder_id,
            limit=payload.limit,
            min_score=0.0,
        )
        results = [
            SearchResultItem(
                video_id=vid,
                s3_key=s3_key,
                title=title,
                description_ai=description_ai,
                score=round(hybrid_score, 4),
                vector_score=round(vector_score, 4),
                fts_score=round(fts_score, 4),
            )
            for vid, s3_key, title, description_ai, hybrid_score, vector_score, fts_score in rows
        ]
    
    return SearchResponse(results=results, query=payload.q, search_mode=payload.search_mode)


@router.get("/search", response_model=SearchResponse)
async def smart_search_get(
    q: str = Query(..., min_length=1),
    folder_id: UUID | None = None,
    limit: int = Query(10, ge=1, le=50),
    search_mode: str = Query("hybrid", pattern="^(hybrid|keyword_boost)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    GET ile arama (arama çubuğu için).
    
    search_mode:
    - "hybrid": Vektör + Full-text search birleşimi (varsayılan)
    - "keyword_boost": Vektör search + keyword boost
    """
    folder_ids = await _user_folder_ids(db, user.id)
    
    if search_mode == "keyword_boost":
        rows = await keyword_boost_search(
            db,
            query_text=q,
            folder_ids=folder_ids,
            folder_id=folder_id,
            limit=limit,
            min_score=0.0,
        )
        results = [
            SearchResultItem(
                video_id=vid,
                s3_key=s3_key,
                title=title,
                description_ai=description_ai,
                score=round(score, 4),
            )
            for vid, s3_key, title, description_ai, score in rows
        ]
    else:
        # Default: hybrid search
        rows = await hybrid_search(
            db,
            query_text=q,
            folder_ids=folder_ids,
            folder_id=folder_id,
            limit=limit,
            min_score=0.0,
        )
        results = [
            SearchResultItem(
                video_id=vid,
                s3_key=s3_key,
                title=title,
                description_ai=description_ai,
                score=round(hybrid_score, 4),
                vector_score=round(vector_score, 4),
                fts_score=round(fts_score, 4),
            )
            for vid, s3_key, title, description_ai, hybrid_score, vector_score, fts_score in rows
        ]
    
    return SearchResponse(results=results, query=q, search_mode=search_mode)
