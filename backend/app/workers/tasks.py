"""
Celery task tanımları - V2 workers/tasks.
Pipeline: Download -> Duplicate Check -> S3 -> Multi-frame Keyframes -> AI Caption -> Transcription -> Embedding -> DB.
"""
import shutil
import tempfile
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.core.db_sync import get_sync_session
from app.models import Tag, Video, VideoStatus, VideoTag
from app.services.ingestion.downloader import download_video
from app.services.ingestion.processor import (
    compute_file_hash,
    extract_keyframes,
    get_duration_seconds,
)
from app.services.intelligence.captioning import caption_from_keyframes
from app.services.intelligence.transcription import transcribe_video
from app.services.intelligence.vectorizer import get_embedding, text_for_embedding
from app.services.storage import upload_file

from .celery_app import celery_app


def _get_downloaded_path(info: dict, output_dir: Path) -> Path | None:
    """
    yt-dlp info'dan indirilen dosya yolunu döner.
    Farklı yt-dlp formatları ve relative path'leri destekler.
    """
    # 1. requested_downloads (merge formatlarda)
    req = info.get("requested_downloads") or []
    for r in req:
        fp = r.get("filepath")
        if fp:
            p = Path(fp)
            if p.exists():
                return p
            # Relative ise output_dir ile birleştir
            if not p.is_absolute():
                full = output_dir / p
                if full.exists():
                    return full

    # 2. info["filename"] veya info["filepath"]
    path = info.get("filename") or info.get("filepath")
    if path:
        p = Path(path)
        if p.exists():
            return p
        if not p.is_absolute():
            full = output_dir / p.name if p.name else output_dir / path
            if full.exists():
                return full
        # output_dir içinde ara (id.ext pattern)
        vid = info.get("id") or "video"
        ext = info.get("ext") or "mp4"
        for candidate in output_dir.glob(f"*.{ext}"):
            return candidate
        for candidate in output_dir.glob("*"):
            if candidate.is_file():
                return candidate
    return None


def _get_video_title(info: dict) -> str:
    """yt-dlp info'dan video başlığını döner."""
    return info.get("title", "") or ""


@celery_app.task(bind=True)
def ingest_video_task(self, video_id: str):
    """
    Video ingestion pipeline V2:
    1. İndir (yt-dlp)
    2. Duplicate kontrolü (hash)
    3. S3'e yükle
    4. Multi-frame keyframe extraction
    5. AI caption (GPT-4o multi-image)
    6. Audio transcription (Whisper)
    7. Embedding üret (title + caption + transcript + tags)
    8. DB güncelle
    """
    video_uuid = UUID(video_id)
    temp_dir = tempfile.mkdtemp(prefix="memevault_")
    keyframes_dir = Path(temp_dir) / "keyframes"
    keyframes_dir.mkdir(exist_ok=True)
    
    try:
        with get_sync_session() as session:
            video = session.get(Video, video_uuid)
            if not video or not video.source_url:
                return {"status": "error", "detail": "Video veya source_url bulunamadı"}
            
            video.status = VideoStatus.PROCESSING
            session.commit()

            # 1. İndir
            print(f"[Task] Video indiriliyor: {video.source_url}")
            try:
                info = download_video(video.source_url, Path(temp_dir))
            except Exception as e:
                video.status = VideoStatus.FAILED
                video.description_ai = f"İndirme hatası: {e}"
                session.commit()
                return {"status": "error", "detail": str(e)}
            
            downloaded_path = _get_downloaded_path(info, Path(temp_dir))
            if not downloaded_path or not downloaded_path.exists():
                video.status = VideoStatus.FAILED
                video.description_ai = "İndirilen dosya bulunamadı"
                session.commit()
                return {"status": "error", "detail": "İndirilen dosya bulunamadı"}
            
            # Video başlığını al
            video_title = _get_video_title(info)
            print(f"[Task] Video başlığı: {video_title}")

            # 2. Hash ve duplicate kontrolü
            file_hash = compute_file_hash(downloaded_path)
            existing_result = session.execute(
                select(Video).where(
                    Video.file_hash == file_hash,
                    Video.id != video_uuid,
                )
            )
            existing = existing_result.scalar_one_or_none()
            if existing:
                # Duplicate: Mevcut videodan tüm metadata'yı kopyala (title, transcript, embedding vb.)
                video.file_hash = file_hash
                video.title = existing.title or video_title
                video.description_ai = existing.description_ai or "Duplicate - zaten mevcut"
                video.transcript = getattr(existing, "transcript", None)
                video.duration = existing.duration
                video.s3_key = existing.s3_key
                video.embedding = existing.embedding
                video.status = VideoStatus.COMPLETED
                session.commit()
                return {"status": "duplicate", "video_id": video_id}

            # 3. Süre
            duration = get_duration_seconds(downloaded_path)
            print(f"[Task] Video süresi: {duration} saniye")

            # 4. S3'e yükle
            ext = downloaded_path.suffix or ".mp4"
            s3_key = f"videos/{video_id}{ext}"
            try:
                upload_file(downloaded_path, s3_key, content_type="video/mp4")
                print(f"[Task] S3'e yüklendi: {s3_key}")
            except Exception as e:
                video.status = VideoStatus.FAILED
                video.description_ai = f"S3 yükleme hatası: {e}"
                session.commit()
                return {"status": "error", "detail": f"S3 upload: {e}"}

            # 5. Multi-frame keyframe extraction ve AI caption
            print("[Task] Keyframe'ler çıkarılıyor...")
            keyframe_paths = extract_keyframes(downloaded_path, keyframes_dir, duration)
            print(f"[Task] {len(keyframe_paths)} keyframe çıkarıldı")
            
            try:
                description_ai = caption_from_keyframes(keyframe_paths)
                print(f"[Task] AI caption oluşturuldu ({len(description_ai)} karakter)")
            except Exception as e:
                description_ai = f"(Caption hatası: {e})"
                print(f"[Task] Caption hatası: {e}")

            # 6. Audio transcription (Whisper) - Config'den kontrol edilir
            from app.core.config import settings
            transcript = ""
            if getattr(settings, 'ENABLE_TRANSCRIPTION', True):
                print("[Task] Ses transkripti oluşturuluyor...")
                try:
                    transcript = transcribe_video(downloaded_path, Path(temp_dir))
                    if transcript:
                        print(f"[Task] Transkript oluşturuldu ({len(transcript)} karakter)")
                    else:
                        print("[Task] Transkript boş veya oluşturulamadı")
                except Exception as e:
                    transcript = ""
                    print(f"[Task] Transkript hatası: {e}")
            else:
                print("[Task] Transkripsiyon devre dışı (ENABLE_TRANSCRIPTION=false)")

            # 7. Etiketleri al (embedding metni için)
            tag_rows = session.execute(
                select(Tag.name).join(VideoTag, VideoTag.tag_id == Tag.id).where(
                    VideoTag.video_id == video_uuid
                )
            ).fetchall()
            tag_names = [r[0] for r in tag_rows]

            # 8. Embedding (title + caption + transcript + tags)
            text = text_for_embedding(
                description_ai=description_ai,
                tags=tag_names,
                title=video_title,
                transcript=transcript
            )
            print(f"[Task] Embedding metni hazırlandı ({len(text)} karakter)")
            
            try:
                embedding = get_embedding(text) if text.strip() else None
                print("[Task] Embedding oluşturuldu")
            except Exception as e:
                embedding = None
                print(f"[Task] Embedding hatası: {e}")

            # 9. DB güncelle
            video.s3_key = s3_key
            video.file_hash = file_hash
            video.duration = duration
            video.title = video_title
            video.description_ai = description_ai
            video.transcript = transcript
            video.status = VideoStatus.COMPLETED
            if embedding is not None:
                video.embedding = embedding
            session.commit()
            
            print(f"[Task] Video işleme tamamlandı: {video_id}")
            return {"status": "ok", "video_id": video_id}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
