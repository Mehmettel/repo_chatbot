"""
Audio transcription - Whisper API ile video sesini metne çevir.
"""
from pathlib import Path

from openai import OpenAI

from app.core.config import settings


def transcribe_audio(audio_path: Path, language: str = "tr") -> str:
    """
    Ses dosyasını OpenAI Whisper API ile metne çevirir.
    
    Args:
        audio_path: Ses dosyasının yolu (mp3, wav, m4a, webm, mp4)
        language: Ses dili (varsayılan: Türkçe)
    
    Returns:
        Transkript metni
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Ses dosyası bulunamadı: {audio_path}")
    
    # Dosya boyutu kontrolü (Whisper max 25MB)
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 25:
        print(f"[Transcription] Dosya çok büyük ({file_size_mb:.1f}MB), transkript atlanıyor")
        return ""
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=language,
                response_format="text"
            )
        return transcript.strip() if transcript else ""
    except Exception as e:
        print(f"[Transcription] Hata: {e}")
        return ""


def transcribe_video(video_path: Path, temp_dir: Path, language: str = "tr") -> str:
    """
    Video dosyasından sesi çıkarıp transkript oluşturur.
    
    Args:
        video_path: Video dosyasının yolu
        temp_dir: Geçici dosyalar için dizin
        language: Ses dili
    
    Returns:
        Transkript metni
    """
    from app.services.ingestion.processor import extract_audio
    
    audio_path = temp_dir / "audio.mp3"
    
    # Sesi çıkar
    extracted = extract_audio(video_path, audio_path)
    if not extracted:
        print("[Transcription] Ses çıkarılamadı")
        return ""
    
    # Transkript oluştur
    return transcribe_audio(audio_path, language)
