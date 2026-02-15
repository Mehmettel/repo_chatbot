"""
Video CRUD ve Upload - BLUEPRINT endpoints/videos.
MVP: Link yapıştır -> Celery ile indir -> S3'e kaydet; thumbnail; klasör/etiket.
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.db import get_db
from app.models import Folder, User, Video, VideoStatus
from app.services.ingestion.downloader import extract_playlist_urls
from app.services.storage import get_presigned_url, delete_file
from app.workers.tasks import ingest_video_task

router = APIRouter()


class VideoCreate(BaseModel):
    source_url: str
    folder_id: UUID  # MVP: her video bir klasörde


class VideoBulkCreate(BaseModel):
    source_urls: list[str]  # Birden fazla URL (her satır veya virgülle ayrılmış)
    folder_id: UUID


class VideoPlaylistCreate(BaseModel):
    playlist_url: str  # YouTube playlist, channel vb.
    folder_id: UUID
    max_entries: int = 50  # Maksimum video sayısı


class VideoUpdate(BaseModel):
    folder_id: Optional[UUID] = None
    description_manual: Optional[str] = None


class VideoResponse(BaseModel):
    id: UUID
    source_url: str | None
    s3_key: str | None
    file_hash: str | None
    title: str | None = None  # V2: Video başlığı
    description_manual: str | None
    description_ai: str | None
    transcript: str | None = None  # V2: Ses transkripti
    duration: int | None
    folder_id: UUID | None
    status: VideoStatus
    created_at: str
    playback_url: str | None = None  # Presigned URL

    class Config:
        from_attributes = True


def _serialize_video(v: Video) -> VideoResponse:
    playback_url = None
    if v.s3_key:
        try:
            playback_url = get_presigned_url(v.s3_key, expires_in=3600)
        except Exception:
            pass
    return VideoResponse(
        id=v.id,
        source_url=v.source_url,
        s3_key=v.s3_key,
        file_hash=v.file_hash,
        title=getattr(v, 'title', None),  # V2 field
        description_manual=v.description_manual,
        description_ai=v.description_ai,
        transcript=getattr(v, 'transcript', None),  # V2 field
        duration=v.duration,
        folder_id=v.folder_id,
        status=v.status,
        created_at=v.created_at.isoformat() if v.created_at else "",
        playback_url=playback_url,
    )


async def _user_folder_ids(db: AsyncSession, user_id: UUID) -> list[UUID]:
    """Kullanıcının tüm klasör id'leri."""
    result = await db.execute(select(Folder.id).where(Folder.user_id == user_id))
    return [r[0] for r in result.all()]


async def _get_user_video(db: AsyncSession, video_id: UUID, user_id: UUID) -> Video | None:
    """Kullanıcıya ait videoyu getir (klasör üzerinden kontrol)."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video or not video.folder_id:
        return None
    
    folder_result = await db.execute(
        select(Folder).where(
            Folder.id == video.folder_id,
            Folder.user_id == user_id,
        )
    )
    if not folder_result.scalar_one_or_none():
        return None
    
    return video


@router.post("/", response_model=VideoResponse)
async def create_video(
    payload: VideoCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Link ile video ekleme; arka planda Celery ile indirme/işleme tetiklenir."""
    result = await db.execute(
        select(Folder).where(
            Folder.id == payload.folder_id,
            Folder.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Klasör bulunamadı veya size ait değil",
        )
    video = Video(
        source_url=payload.source_url,
        folder_id=payload.folder_id,
        status=VideoStatus.PENDING,
    )
    db.add(video)
    await db.flush()
    await db.refresh(video)
    ingest_video_task.delay(str(video.id))
    return _serialize_video(video)


@router.post("/bulk")
async def create_videos_bulk(
    payload: VideoBulkCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Toplu video ekleme. Birden fazla URL tek seferde eklenir.
    Her URL ayrı bir video kaydı oluşturur ve Celery ile işlenir.
    """
    result = await db.execute(
        select(Folder).where(
            Folder.id == payload.folder_id,
            Folder.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Klasör bulunamadı veya size ait değil",
        )

    # URL'leri normalize et (boş satırları, virgülleri ayır)
    urls = []
    for raw in payload.source_urls:
        for part in raw.replace(",", "\n").split():
            u = part.strip()
            if u and u.startswith(("http://", "https://")):
                urls.append(u)

    # Tekrarları kaldır, sırayı koru
    seen = set()
    unique_urls = [u for u in urls if u not in seen and not seen.add(u)]

    if not unique_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçerli video URL'si bulunamadı",
        )
    if len(unique_urls) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="En fazla 100 video tek seferde eklenebilir",
        )

    # Önce tüm video kayıtlarını oluştur
    created = []
    video_ids = []
    for url in unique_urls:
        video = Video(
            source_url=url,
            folder_id=payload.folder_id,
            status=VideoStatus.PENDING,
        )
        db.add(video)
        await db.flush()
        await db.refresh(video)
        video_ids.append(str(video.id))
        created.append(_serialize_video(video))

    # Commit ile veritabanına kaydet
    await db.commit()
    
    # Şimdi task'ları tetikle (artık videolar DB'de mevcut)
    task_results = []
    for video_id in video_ids:
        try:
            result = ingest_video_task.delay(video_id)
            task_results.append({
                "video_id": video_id,
                "task_id": result.id if result else None,
                "queued": True
            })
        except Exception as e:
            # Task tetikleme hatası - videoyu PENDING bırak
            task_results.append({
                "video_id": video_id,
                "error": str(e),
                "queued": False
            })

    return {
        "created": len(created),
        "videos": created,
        "tasks_queued": sum(1 for t in task_results if t.get("queued")),
        "tasks_failed": sum(1 for t in task_results if not t.get("queued"))
    }


@router.post("/from-playlist")
async def create_videos_from_playlist(
    payload: VideoPlaylistCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Playlist URL'sinden videoları toplu ekler.
    YouTube playlist, channel vb. desteklenir (yt-dlp ile).
    """
    result = await db.execute(
        select(Folder).where(
            Folder.id == payload.folder_id,
            Folder.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Klasör bulunamadı veya size ait değil",
        )

    urls = extract_playlist_urls(payload.playlist_url, max_entries=payload.max_entries)
    if not urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Playlist'ten video URL'si çıkarılamadı. Geçerli bir playlist linki girin.",
        )

    # Önce tüm video kayıtlarını oluştur
    created = []
    video_ids = []
    for url in urls:
        video = Video(
            source_url=url,
            folder_id=payload.folder_id,
            status=VideoStatus.PENDING,
        )
        db.add(video)
        await db.flush()
        await db.refresh(video)
        video_ids.append(str(video.id))
        created.append(_serialize_video(video))

    # Commit ile veritabanına kaydet
    await db.commit()
    
    # Şimdi task'ları tetikle (artık videolar DB'de mevcut)
    task_results = []
    for video_id in video_ids:
        try:
            result = ingest_video_task.delay(video_id)
            task_results.append({
                "video_id": video_id,
                "task_id": result.id if result else None,
                "queued": True
            })
        except Exception as e:
            # Task tetikleme hatası - videoyu PENDING bırak
            task_results.append({
                "video_id": video_id,
                "error": str(e),
                "queued": False
            })

    tasks_queued = sum(1 for t in task_results if t.get("queued"))
    tasks_failed = sum(1 for t in task_results if not t.get("queued"))

    return {
        "created": len(created),
        "videos": created,
        "tasks_queued": tasks_queued,
        "tasks_failed": tasks_failed,
        "message": f"{tasks_queued}/{len(created)} video kuyruğa eklendi" + (f", {tasks_failed} başarısız" if tasks_failed > 0 else "")
    }


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Video detayı (sadece kendi klasörlerinizdeki videolar)."""
    video = await _get_user_video(db, video_id, user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video bulunamadı",
        )
    return _serialize_video(video)


@router.get("/", response_model=list[VideoResponse])
async def list_videos(
    folder_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Video listesi; opsiyonel folder_id filtresi (sadece kendi klasörleriniz)."""
    folder_ids = await _user_folder_ids(db, user.id)
    if not folder_ids:
        return []
    q = select(Video).where(Video.folder_id.in_(folder_ids))
    if folder_id is not None:
        if folder_id not in folder_ids:
            return []
        q = q.where(Video.folder_id == folder_id)
    result = await db.execute(q.order_by(Video.created_at.desc()))
    videos = result.scalars().all()
    return [_serialize_video(v) for v in videos]


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: UUID,
    payload: VideoUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Video güncelle (klasör değiştir/taşı, açıklama ekle)."""
    video = await _get_user_video(db, video_id, user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video bulunamadı",
        )
    
    # Klasör değiştirme (taşıma)
    if payload.folder_id is not None:
        # Hedef klasörün kullanıcıya ait olduğunu kontrol et
        folder_result = await db.execute(
            select(Folder).where(
                Folder.id == payload.folder_id,
                Folder.user_id == user.id,
            )
        )
        if not folder_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hedef klasör bulunamadı",
            )
        video.folder_id = payload.folder_id
    
    # Manuel açıklama güncelleme
    if payload.description_manual is not None:
        video.description_manual = payload.description_manual
    
    await db.flush()
    await db.refresh(video)
    return _serialize_video(video)


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Videoyu sil (S3'den de siler)."""
    video = await _get_user_video(db, video_id, user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video bulunamadı",
        )
    
    # S3'den dosyayı sil
    if video.s3_key:
        try:
            delete_file(video.s3_key)
        except Exception as e:
            # S3 silme hatası olsa bile devam et
            print(f"S3 silme hatası: {e}")
    
    # Veritabanından sil
    await db.delete(video)
    await db.flush()
    return None


@router.post("/{video_id}/retry", response_model=VideoResponse)
async def retry_video(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Bekleyen veya başarısız videoyu yeniden işle."""
    video = await _get_user_video(db, video_id, user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video bulunamadı",
        )
    
    if video.status not in [VideoStatus.PENDING, VideoStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece bekleyen veya başarısız videolar yeniden işlenebilir",
        )
    
    # Durumu PENDING'e çevir ve görevi yeniden tetikle
    video.status = VideoStatus.PENDING
    video.description_ai = None
    await db.flush()
    await db.refresh(video)
    
    ingest_video_task.delay(str(video.id))
    return _serialize_video(video)


@router.post("/retry-all-pending")
async def retry_all_pending(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Tüm bekleyen videoları yeniden işle."""
    folder_ids = await _user_folder_ids(db, user.id)
    if not folder_ids:
        return {"retried": 0, "video_ids": []}
    
    result = await db.execute(
        select(Video).where(
            Video.folder_id.in_(folder_ids),
            Video.status.in_([VideoStatus.PENDING, VideoStatus.FAILED]),
        )
    )
    videos = result.scalars().all()
    
    retried_ids = []
    for video in videos:
        video.status = VideoStatus.PENDING
        ingest_video_task.delay(str(video.id))
        retried_ids.append(str(video.id))
    
    await db.flush()
    return {"retried": len(retried_ids), "video_ids": retried_ids}


@router.post("/reprocess-all")
async def reprocess_all_videos(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Tüm tamamlanmış videoları V2 pipeline ile yeniden işle.
    
    Bu işlem:
    - Multi-frame keyframe extraction
    - Gelişmiş AI caption (multi-image GPT-4o)
    - Audio transcription (Whisper)
    - Hybrid search için yeni embedding
    
    NOT: Bu işlem API maliyetine neden olur ve uzun sürebilir.
    """
    folder_ids = await _user_folder_ids(db, user.id)
    if not folder_ids:
        return {"queued": 0, "video_ids": [], "message": "Hiç video bulunamadı"}
    
    # Sadece COMPLETED videoları al (yeniden işlenecek)
    result = await db.execute(
        select(Video).where(
            Video.folder_id.in_(folder_ids),
            Video.status == VideoStatus.COMPLETED,
            Video.source_url.isnot(None),  # source_url olmalı (yeniden indirilecek)
        )
    )
    videos = result.scalars().all()
    
    queued_ids = []
    for video in videos:
        # Durumu PENDING'e çevir
        video.status = VideoStatus.PENDING
        # Eski verileri temizle (yeniden oluşturulacak)
        video.description_ai = None
        video.transcript = None
        video.title = None
        video.embedding = None
        video.search_vector = None
        # Görevi tetikle
        ingest_video_task.delay(str(video.id))
        queued_ids.append(str(video.id))
    
    await db.flush()
    
    return {
        "queued": len(queued_ids),
        "video_ids": queued_ids,
        "message": f"{len(queued_ids)} video V2 pipeline ile yeniden işlenmeye başladı"
    }


@router.post("/{video_id}/reprocess", response_model=VideoResponse)
async def reprocess_single_video(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Tek bir videoyu V2 pipeline ile yeniden işle.
    Video tamamlanmış olsa bile yeniden işlenir.
    """
    video = await _get_user_video(db, video_id, user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video bulunamadı",
        )
    
    if not video.source_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video source_url'i yok, yeniden işlenemez",
        )
    
    # Durumu PENDING'e çevir ve eski verileri temizle
    video.status = VideoStatus.PENDING
    video.description_ai = None
    video.transcript = None
    video.title = None
    video.embedding = None
    video.search_vector = None
    
    await db.flush()
    await db.refresh(video)
    
    # Görevi tetikle
    ingest_video_task.delay(str(video.id))
    
    return _serialize_video(video)
