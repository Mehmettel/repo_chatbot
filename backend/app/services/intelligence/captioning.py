"""
Vision LLM entegrasyonu - Video keyframe'ler -> metin açıklama.
Multi-frame analiz ile gelişmiş video understanding.
"""
import base64
from pathlib import Path

from openai import OpenAI

from app.core.config import settings

# Gelişmiş caption prompt - daha kapsamlı ve aranabilir açıklamalar için
SINGLE_FRAME_PROMPT = """Bu video karesini analiz et ve şunları detaylıca açıkla:

1. SAHNEDEKİ AKSİYON: Ne oluyor? Kim ne yapıyor? Hangi hareket/eylem var?
2. KARAKTERLER: Kaç kişi var? Cinsiyetleri? Ne giyiyorlar? Fiziksel özellikleri?
3. MEKAN/ORTAM: Nerede geçiyor? (stadyum, ev, ofis, sokak, cafe, spor salonu vb.)
4. NESNELER: Önemli objeler neler? (top, telefon, araba, yemek, bilgisayar vb.)
5. DUYGUSAL TON: Komik mi, ciddi mi, dramatik mi, heyecanlı mı?
6. METİNLER: Ekranda yazı varsa ne yazıyor?

Türkçe olarak detaylı, aranabilir ve açıklayıcı bir metin yaz. Önemli anahtar kelimeleri kullan."""

MULTI_FRAME_PROMPT = """Bu video karelerini analiz et. Kareler videonun başından sonuna doğru sıralı olarak verilmiştir.

Her kareyi inceleyerek videonun tamamını anlat:

1. VİDEONUN KONUSU: Video ne hakkında? Ana tema nedir?
2. OLAY AKIŞI: Baştan sona ne oluyor? Nasıl bir hikaye/aksiyon var?
3. KARAKTERLER: Kimler var? Ne yapıyorlar? Fiziksel özellikleri?
4. MEKAN: Nerede geçiyor? (stadyum, ev, ofis, sokak, cafe, spor salonu, futbol sahası vb.)
5. ÖNEMLİ ANLAR: Dikkat çekici, komik veya önemli sahneler neler?
6. NESNELER: Önemli objeler neler? (top, telefon, araba, yemek vb.)
7. METİNLER: Ekranda yazı varsa neler yazıyor?

Türkçe olarak detaylı, aranabilir ve kapsamlı bir açıklama yaz. Spor, komedi, drama gibi içerik türünü belirt."""


def _encode_image(image_path: Path) -> str:
    """Görseli base64 formatına çevirir."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def caption_image(image_path: Path) -> str:
    """
    Tek görsel dosyasını (thumbnail) multimodal LLM ile metne döker.
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Görsel bulunamadı: {image_path}")
    
    b64 = _encode_image(image_path)
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    resp = client.chat.completions.create(
        model=settings.CAPTION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": SINGLE_FRAME_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }
        ],
        max_tokens=800,
    )
    return (resp.choices[0].message.content or "").strip()


def caption_from_keyframes(keyframe_paths: list[Path]) -> str:
    """
    Birden fazla keyframe'i tek API çağrısında analiz eder.
    GPT-4o'nun multi-image özelliğini kullanarak tüm videoyu anlar.
    """
    if not keyframe_paths:
        return ""
    
    # Mevcut dosyaları filtrele
    valid_paths = [p for p in keyframe_paths if p.exists()]
    
    if not valid_paths:
        return ""
    
    # Tek frame varsa basit analiz
    if len(valid_paths) == 1:
        return caption_image(valid_paths[0])
    
    # Multi-frame analiz
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Content listesi oluştur: önce prompt, sonra tüm görseller
    content = [{"type": "text", "text": MULTI_FRAME_PROMPT}]
    
    for i, path in enumerate(valid_paths):
        b64 = _encode_image(path)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64}",
                "detail": "low"  # Maliyet optimizasyonu için low detail
            }
        })
    
    try:
        resp = client.chat.completions.create(
            model=settings.CAPTION_MODEL,
            messages=[{"role": "user", "content": content}],
            max_tokens=1200,  # Multi-frame için daha fazla token
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"[Caption] Multi-frame analiz hatası: {e}")
        # Fallback: İlk frame'i analiz et
        return caption_image(valid_paths[0])
