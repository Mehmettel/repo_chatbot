"""
yt-dlp wrapper - BLUEPRINT: Link doğrulama ve en iyi kalitede indirme.
"""
import os
import shutil
from pathlib import Path
from typing import Any

import yt_dlp

from app.core.config import settings


def _get_ffmpeg_location() -> str | None:
    """FFmpeg konumunu tespit et."""
    # 1. Backend klasöründeki ffmpeg.exe (mutlak yol ile)
    # downloader.py -> ingestion -> services -> app -> backend
    backend_dir = Path(__file__).resolve().parent.parent.parent.parent
    local_ffmpeg = backend_dir / "ffmpeg.exe"
    
    if local_ffmpeg.exists():
        print(f"[FFmpeg] Backend'de bulundu: {backend_dir}")
        return str(backend_dir)
    
    # 2. Çalışma dizininde ara
    cwd_ffmpeg = Path.cwd() / "ffmpeg.exe"
    if cwd_ffmpeg.exists():
        print(f"[FFmpeg] CWD'de bulundu: {Path.cwd()}")
        return str(Path.cwd())
    
    # 3. Sistem PATH'inde ara
    if shutil.which("ffmpeg"):
        print("[FFmpeg] Sistem PATH'inde bulundu")
        return None  # PATH'de var, yt-dlp otomatik bulur
    
    print(f"[FFmpeg] BULUNAMADI! Backend dir: {backend_dir}, CWD: {Path.cwd()}")
    return None


def download_video(
    url: str,
    output_dir: Path,
    output_template: str | None = None,
) -> dict[str, Any]:
    """
    Verilen URL'den videoyu indirir.
    Returns: info dict (id, title, duration, file path, vb.).
    """
    template = output_template or settings.YT_DLP_OUTPUT_TEMPLATE
    # yt-dlp outtmpl: dizin + şablon örn. "%(id)s.%(ext)s"
    out_tmpl = str(Path(output_dir) / template)

    # FFmpeg konumunu tespit et
    ffmpeg_loc = _get_ffmpeg_location()
    
    ydl_opts = {
        "outtmpl": out_tmpl,
        "quiet": False,
    }
    
    # FFmpeg varsa en iyi kalite (birleştirmeli), yoksa tek format
    if ffmpeg_loc:
        ydl_opts["ffmpeg_location"] = ffmpeg_loc
        ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        ydl_opts["merge_output_format"] = "mp4"
    else:
        # FFmpeg yoksa birleştirme gerektirmeyen en iyi format
        ydl_opts["format"] = "best[ext=mp4]/best"
        print("[yt-dlp] FFmpeg bulunamadı, birleştirme gerektirmeyen format kullanılıyor")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise ValueError(f"Indirme basarisiz: {url}")
        return info


def validate_url(url: str) -> bool:
    """Linkin desteklenen bir platforma ait olup olmadığını sadece kontrol eder (indirme yapmaz)."""
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
            ydl.extract_info(url, download=False)
        return True
    except Exception:
        return False


def extract_playlist_urls(playlist_url: str, max_entries: int = 50) -> list[str]:
    """
    Playlist URL'sinden video URL'lerini çıkarır (indirme yapmaz).
    
    Args:
        playlist_url: YouTube playlist, channel vb. URL
        max_entries: Maksimum video sayısı (varsayılan 50)
    
    Returns:
        Video URL'leri listesi
    """
    urls = []
    try:
        opts = {
            "quiet": True,
            "extract_flat": "in_playlist",
            "playlistend": max_entries,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            if not info:
                return []
            entries = info.get("entries") or []
            for e in entries:
                if not e:
                    continue
                # Önce tam URL varsa kullan
                u = e.get("url") or e.get("webpage_url")
                if u and u.startswith("http"):
                    urls.append(u)
                    continue
                # YouTube: id'den URL oluştur
                vid = e.get("id")
                if vid:
                    urls.append(f"https://www.youtube.com/watch?v={vid}")
            return urls[:max_entries]
    except Exception as e:
        print(f"[Playlist] Hata: {e}")
        return []
