"""
MemeVault API kullanım örneği - Python client.
BLUEPRINT MVP akışı: Register -> Login -> Folder oluştur -> Video ekle -> Arama yap.
"""
import time

import requests

BASE_URL = "http://localhost:8000/api/v1"


def register(email: str, password: str) -> str:
    """Kullanıcı kaydı, token döner."""
    resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def login(email: str, password: str) -> str:
    """Giriş, token döner."""
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_folder(token: str, name: str, parent_id: str | None = None) -> dict:
    """Klasör oluştur."""
    resp = requests.post(
        f"{BASE_URL}/folders/",
        json={"name": name, "parent_id": parent_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


def list_folders(token: str) -> list[dict]:
    """Klasörleri listele."""
    resp = requests.get(
        f"{BASE_URL}/folders/",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


def create_video(token: str, source_url: str, folder_id: str) -> dict:
    """Video ekle (Celery ile indirme başlar)."""
    resp = requests.post(
        f"{BASE_URL}/videos/",
        json={"source_url": source_url, "folder_id": folder_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


def get_video(token: str, video_id: str) -> dict:
    """Video detayı (status kontrolü için)."""
    resp = requests.get(
        f"{BASE_URL}/videos/{video_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


def search_videos(token: str, query: str, limit: int = 10) -> dict:
    """Akıllı arama (semantik)."""
    resp = requests.get(
        f"{BASE_URL}/chat/search",
        params={"q": query, "limit": limit},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


def create_tag(token: str, name: str) -> dict:
    """Etiket oluştur."""
    resp = requests.post(
        f"{BASE_URL}/tags/",
        json={"name": name, "type": "MANUAL"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


def attach_tag(token: str, video_id: str, tag_id: str):
    """Videoya etiket ekle."""
    resp = requests.post(
        f"{BASE_URL}/tags/attach",
        json={"video_id": video_id, "tag_id": tag_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()


if __name__ == "__main__":
    # 1. Kayıt veya giriş
    email = "test@example.com"
    password = "test123"
    try:
        token = register(email, password)
        print(f"[OK] Kayit basarili, token alindi")
    except requests.HTTPError:
        token = login(email, password)
        print(f"[OK] Giris basarili, token alindi")

    # 2. Klasor olustur
    folder = create_folder(token, "Komik Videolar")
    print(f"[OK] Klasor olusturuldu: {folder['name']} ({folder['id']})")

    # 3. Video ekle (ornek: YouTube kisa link)
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    video = create_video(token, video_url, folder["id"])
    print(f"[OK] Video eklendi: {video['id']}, durum: {video['status']}")

    # 4. Islem durumu kontrol (opsiyonel: poll)
    print("Celery islemi bekle (30sn)...")
    for i in range(6):
        time.sleep(5)
        v = get_video(token, video["id"])
        print(f"  [{i*5}s] Durum: {v['status']}")
        if v["status"] in ("COMPLETED", "FAILED"):
            break

    # 5. Etiket ekle
    tag = create_tag(token, "komik")
    print(f"[OK] Etiket olusturuldu: {tag['name']}")
    attach_tag(token, video["id"], tag["id"])
    print(f"[OK] Etiket videoya eklendi")

    # 6. Arama yap
    search_result = search_videos(token, "komik video")
    print(f"[OK] Arama sonucu: {len(search_result['results'])} video bulundu")
    for res in search_result["results"][:3]:
        print(f"  - {res['video_id']}: {res['description_ai'][:60]}... (skor: {res['score']})")
        if res.get("playback_url"):
            print(f"    Izle: {res['playback_url'][:80]}...")
