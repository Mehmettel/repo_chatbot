"""
Etiket yönetimi - BLUEPRINT: Tag (MANUAL | AI_GENERATED), VideoTags pivot.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.db import get_db
from app.models import Folder, Tag, TagType, User, Video, VideoTag

router = APIRouter()


class TagCreate(BaseModel):
    name: str
    type: TagType = TagType.MANUAL


class TagResponse(BaseModel):
    id: UUID
    name: str
    type: TagType

    class Config:
        from_attributes = True


class VideoTagAttach(BaseModel):
    video_id: UUID
    tag_id: UUID


@router.post("/", response_model=TagResponse)
async def create_tag(
    payload: TagCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Etiket oluştur (veya mevcut etiketi döner)."""
    result = await db.execute(
        select(Tag).where(Tag.name == payload.name, Tag.type == payload.type)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return TagResponse(id=existing.id, name=existing.name, type=existing.type)
    tag = Tag(name=payload.name, type=payload.type)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return TagResponse(id=tag.id, name=tag.name, type=tag.type)


@router.get("/", response_model=list[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Tüm etiketleri listele."""
    result = await db.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    return [TagResponse(id=t.id, name=t.name, type=t.type) for t in tags]


@router.post("/attach", status_code=status.HTTP_204_NO_CONTENT)
async def attach_tag_to_video(
    payload: VideoTagAttach,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Videoya etiket ekle (video kullanıcının klasöründe olmalı)."""
    video_result = await db.execute(select(Video).where(Video.id == payload.video_id))
    video = video_result.scalar_one_or_none()
    if not video or not video.folder_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video bulunamadı",
        )
    folder_result = await db.execute(
        select(Folder).where(Folder.id == video.folder_id, Folder.user_id == user.id)
    )
    if not folder_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video bulunamadı",
        )
    tag_result = await db.execute(select(Tag).where(Tag.id == payload.tag_id))
    if not tag_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etiket bulunamadı",
        )
    existing_vt = await db.execute(
        select(VideoTag).where(
            VideoTag.video_id == payload.video_id,
            VideoTag.tag_id == payload.tag_id,
        )
    )
    if existing_vt.scalar_one_or_none():
        return
    vt = VideoTag(video_id=payload.video_id, tag_id=payload.tag_id)
    db.add(vt)
    await db.flush()


@router.delete("/detach", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag_from_video(
    payload: VideoTagAttach,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Videodan etiket çıkar."""
    video_result = await db.execute(select(Video).where(Video.id == payload.video_id))
    video = video_result.scalar_one_or_none()
    if not video or not video.folder_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video bulunamadı",
        )
    folder_result = await db.execute(
        select(Folder).where(Folder.id == video.folder_id, Folder.user_id == user.id)
    )
    if not folder_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video bulunamadı",
        )
    vt_result = await db.execute(
        select(VideoTag).where(
            VideoTag.video_id == payload.video_id,
            VideoTag.tag_id == payload.tag_id,
        )
    )
    vt = vt_result.scalar_one_or_none()
    if vt:
        await db.delete(vt)
        await db.flush()


@router.get("/video/{video_id}", response_model=list[TagResponse])
async def get_video_tags(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Video etiketlerini listele."""
    video_result = await db.execute(select(Video).where(Video.id == video_id))
    video = video_result.scalar_one_or_none()
    if not video or not video.folder_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video bulunamadı",
        )
    folder_result = await db.execute(
        select(Folder).where(Folder.id == video.folder_id, Folder.user_id == user.id)
    )
    if not folder_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video bulunamadı",
        )
    tag_rows = await db.execute(
        select(Tag)
        .join(VideoTag, VideoTag.tag_id == Tag.id)
        .where(VideoTag.video_id == video_id)
    )
    tags = tag_rows.scalars().all()
    return [TagResponse(id=t.id, name=t.name, type=t.type) for t in tags]
