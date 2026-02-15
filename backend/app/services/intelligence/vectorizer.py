"""
Embedding yönetimi - description_ai + title + transcript + etiketler -> vektör; pgvector.
OpenAI text-embedding-3-small.
V2: Gelişmiş metin birleştirme ile daha iyi arama doğruluğu.
"""
from typing import List

from openai import OpenAI

from app.core.config import settings


def get_embedding(text: str) -> List[float]:
    """
    Metni OpenAI text-embedding-3-small ile vektöre çevirir.
    """
    if not text.strip():
        raise ValueError("Embedding için boş metin gönderilemez")
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text.strip(),
    )
    return resp.data[0].embedding


def text_for_embedding(
    description_ai: str,
    tags: list[str],
    title: str = "",
    transcript: str = ""
) -> str:
    """
    Video için aranabilir metin oluşturur.
    Tüm metin kaynaklarını birleştirerek zengin bir embedding metni üretir.
    
    Öncelik sırası:
    1. Başlık (en önemli - arama terimlerine en yakın)
    2. AI açıklaması (görsel içerik)
    3. Transkript (sesli içerik)
    4. Etiketler (kullanıcı tanımlı kategoriler)
    """
    parts = []
    
    # Başlık - genellikle en önemli anahtar kelimeleri içerir
    if title and title.strip():
        parts.append(f"Başlık: {title.strip()}")
    
    # AI açıklaması - görsel içeriğin detaylı tasviri
    if description_ai and description_ai.strip():
        parts.append(f"Açıklama: {description_ai.strip()}")
    
    # Transkript - videodaki konuşmalar
    if transcript and transcript.strip():
        # Çok uzun transkriptleri kısalt (embedding limitleri için)
        transcript_text = transcript.strip()
        if len(transcript_text) > 2000:
            transcript_text = transcript_text[:2000] + "..."
        parts.append(f"Konuşmalar: {transcript_text}")
    
    # Etiketler
    if tags:
        parts.append(f"Etiketler: {' '.join(tags)}")
    
    return "\n".join(parts).strip() or ""
