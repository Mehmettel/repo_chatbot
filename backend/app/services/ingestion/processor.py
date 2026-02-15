"""
FFMPEG işlemleri: Normalizer (standart MP4, thumbnail) ve Duplicate Check (file hash).
BLUEPRINT: Normalizer, Duplicate Checker.
"""
import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.core.config import settings


def _get_ffmpeg_path() -> str:
    """FFmpeg yolunu tespit et."""
    # 1. Backend klasöründeki ffmpeg.exe
    backend_dir = Path(__file__).parent.parent.parent.parent  # backend/
    local_ffmpeg = backend_dir / "ffmpeg.exe"
    if local_ffmpeg.exists():
        return str(local_ffmpeg)
    
    # 2. Sistem PATH'inde ara
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    
    return "ffmpeg"  # Default, hata verirse anlaşılır


def _get_ffprobe_path() -> str:
    """FFprobe yolunu tespit et."""
    # 1. Backend klasöründeki ffprobe.exe
    backend_dir = Path(__file__).parent.parent.parent.parent  # backend/
    local_ffprobe = backend_dir / "ffprobe.exe"
    if local_ffprobe.exists():
        return str(local_ffprobe)
    
    # 2. Sistem PATH'inde ara
    system_ffprobe = shutil.which("ffprobe")
    if system_ffprobe:
        return system_ffprobe
    
    return "ffprobe"  # Default


def compute_file_hash(file_path: Path) -> str:
    """SHA-256 ile dosya hash'i; duplicate kontrolü için."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_video(
    input_path: Path,
    output_path: Path,
    format: str | None = None,
) -> Path:
    """
    Videoyu standart formata (MP4, h.264) dönüştürür.
    Transcoding: BLUEPRINT risk azaltma (720p Mobile vb.).
    """
    fmt = format or settings.DEFAULT_VIDEO_FORMAT
    ffmpeg = _get_ffmpeg_path()
    cmd = [
        ffmpeg,
        "-y",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-vf", "scale=-2:720",  # 720p
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def extract_thumbnail(video_path: Path, output_path: Path, time_sec: float = 0.0) -> Path:
    """Videodan tek kare (thumbnail) alır. MVP: ilk kare veya belirtilen saniye."""
    ffmpeg = _get_ffmpeg_path()
    cmd = [
        ffmpeg,
        "-y",
        "-ss", str(time_sec),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


# Keyframe extraction - config'den ayarlanabilir
def _get_keyframe_percentages() -> list[float]:
    """
    Config'deki KEYFRAME_COUNT'a göre yüzde değerleri döner.
    1: [0.5] - sadece orta
    2: [0.25, 0.75] - çeyrekler
    3: [0.1, 0.5, 0.9] - başlangıç, orta, son (önerilen)
    4: [0.1, 0.35, 0.65, 0.9]
    5: [0.0, 0.25, 0.5, 0.75, 0.95]
    """
    from app.core.config import settings
    count = getattr(settings, 'KEYFRAME_COUNT', 3)
    
    if count <= 1:
        return [0.5]
    elif count == 2:
        return [0.25, 0.75]
    elif count == 3:
        return [0.1, 0.5, 0.9]
    elif count == 4:
        return [0.1, 0.35, 0.65, 0.9]
    else:  # 5+
        return [0.0, 0.25, 0.5, 0.75, 0.95]


def extract_keyframes(
    video_path: Path, 
    output_dir: Path, 
    duration_seconds: int | None = None
) -> list[Path]:
    """
    Videonun farklı anlarından keyframe'ler çıkarır.
    Config'deki KEYFRAME_COUNT ayarına göre kare sayısı belirlenir.
    
    Returns: Çıkarılan keyframe dosyalarının yolları listesi
    """
    # Video süresini al (verilmediyse hesapla)
    if duration_seconds is None:
        duration_seconds = get_duration_seconds(video_path)
    
    if not duration_seconds or duration_seconds <= 0:
        # Süre alınamadıysa sadece orta kareyi al
        single_frame = output_dir / "keyframe_0.jpg"
        extract_thumbnail(video_path, single_frame, time_sec=0.5)
        return [single_frame] if single_frame.exists() else []
    
    keyframes = []
    ffmpeg = _get_ffmpeg_path()
    keyframe_percentages = _get_keyframe_percentages()
    
    for i, percentage in enumerate(keyframe_percentages):
        time_sec = duration_seconds * percentage
        # Son kare için biraz geriye gel (video sonunda sorun olmaması için)
        if percentage >= 0.95:
            time_sec = max(0, duration_seconds - 0.5)
        
        output_path = output_dir / f"keyframe_{i}.jpg"
        
        try:
            cmd = [
                ffmpeg,
                "-y",
                "-ss", str(time_sec),
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(output_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            if output_path.exists():
                keyframes.append(output_path)
        except Exception as e:
            print(f"[Keyframe] {percentage*100:.0f}% karesinde hata: {e}")
            continue
    
    return keyframes


def extract_audio(video_path: Path, output_path: Path) -> Path | None:
    """
    Videodan ses dosyasını çıkarır (Whisper için).
    Returns: Ses dosyası yolu veya None (hata durumunda)
    """
    ffmpeg = _get_ffmpeg_path()
    try:
        cmd = [
            ffmpeg,
            "-y",
            "-i", str(video_path),
            "-vn",  # Video yok
            "-acodec", "libmp3lame",
            "-ar", "16000",  # 16kHz (Whisper için optimal)
            "-ac", "1",  # Mono
            "-b:a", "64k",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path if output_path.exists() else None
    except Exception as e:
        print(f"[Audio] Ses çıkarma hatası: {e}")
        return None


def get_duration_seconds(video_path: Path) -> int | None:
    """ffprobe ile süre (saniye) döner."""
    ffprobe = _get_ffprobe_path()
    cmd = [
        ffprobe,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return int(float(out.stdout.strip()))
    except Exception:
        return None
