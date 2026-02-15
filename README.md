# MemeVault

**AI destekli video arşivi.** YouTube, Instagram, TikTok gibi platformlardan videoları ekleyin; doğal dil ile anlam bazlı arama yapın.

**Repo:** [github.com/Mehmettel/repo_chatbot](https://github.com/Mehmettel/repo_chatbot)

---

## Ne Yapar?

- Video linki (tek, toplu veya playlist) ekleme
- Videoları klasörlerde toplama
- **Akıllı arama:** "maça girmeye hazırlanan adam", "komik kediler" gibi cümlelerle bulma
- Video başlığı, AI açıklaması, ses transkripti (Whisper)
- Hybrid arama (vektör + full-text)

---

## Dokümantasyon

| Dosya | Açıklama |
|-------|----------|
| [KULLANICI_KILAVUZU.md](KULLANICI_KILAVUZU.md) | Kullanıcı kılavuzu — ne işe yarar, nasıl kullanılır |
| [BLUEPRINT.md](BLUEPRINT.md) | Mimari plan (Modular Monolith, MVP/Faz 2) |

---

## Hızlı Başlangıç

### Gereksinimler

- **Docker Desktop** (PostgreSQL, Redis, MinIO)
- **Python 3.11+**
- **Node.js 18+**
- **FFmpeg** (video işleme)
- **OpenAI API anahtarı**

### 1. Repoyu klonlayın

```bash
git clone https://github.com/Mehmettel/repo_chatbot.git
cd repo_chatbot
```

### 2. Backend ortamı

```bash
cd backend
cp .env.example .env
# .env dosyasını düzenleyin: OPENAI_API_KEY, isteğe bağlı SECRET_KEY
pip install -r requirements.txt
# veya: python -m venv venv && venv\Scripts\activate (Windows)
```

**Önemli:** `.env` dosyası şifre ve API anahtarı içerir; **asla** repoya eklenmez. `.env.example` şablon olarak kullanılır.

### 3. Veritabanı ve servisler

```bash
docker-compose up -d postgres redis minio
cd backend && alembic upgrade head
```

### 4. Backend API

```bash
cd backend
set PYTHONPATH=%CD%   # Windows
# export PYTHONPATH=. # Linux/macOS
uvicorn app.main:app --reload
```

### 5. Celery worker (video işleme)

Ayrı bir terminalde:

```bash
cd backend
set PYTHONPATH=%CD%
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

Windows’ta `--pool=solo` kullanılmalı.

### 6. Frontend

```bash
cd frontend
npm install
npm run dev
```

Tarayıcıda: **http://localhost:5173**

---

## Örnek hesap

İlk çalıştırmada API, örnek kullanıcıyı otomatik oluşturur.

- **E-posta:** `deneme@gmail.com`
- **Şifre:** `deneme`

Manuel oluşturmak için: `cd backend && python -m app.seed_user`

---

## Proje yapısı

```
repo_chatbot/
├── backend/          # FastAPI, Celery, PostgreSQL (pgvector), Redis, S3/MinIO
│   ├── app/
│   ├── alembic/
│   ├── .env.example  # Şablon — .env buradan kopyalanır (repoda .env yok)
│   └── requirements.txt
├── frontend/         # React (Vite), Tailwind
├── examples/         # Python API client, HTML demo
├── BLUEPRINT.md
├── KULLANICI_KILAVUZU.md
└── README.md
```

---

## API özeti

- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- `POST/GET /api/v1/folders/`
- `POST /api/v1/videos/` — tek video
- `POST /api/v1/videos/bulk` — toplu URL
- `POST /api/v1/videos/from-playlist` — playlist
- `GET /api/v1/videos/`, `GET /api/v1/videos/{id}`
- `GET /api/v1/chat/search?q=...` — akıllı arama (Bearer token gerekli)
- `POST /api/v1/videos/{id}/retry` — başarısız videoyu yeniden işleme

---

## Lisans

Bu proje eğitim ve kişisel kullanım amaçlıdır. OpenAI API kullanımı kendi kullanım koşullarınıza tabidir.
