# MemeVault: AI Destekli Mizahi Video Arşivi — Mimari Plan

**Proje:** [github.com/Mehmettel/repo_chatbot](https://github.com/Mehmettel/repo_chatbot)  
**Sürüm:** 1.0.0  
**Durum:** Taslak (Draft)  
**Mimari Yaklaşım:** Modular Monolith (Python/FastAPI) + Event-Driven Ingestion

---

## 1. Sistem Mimarisi

Projenin ölçeklenebilirliği, bakım kolaylığı ve AI entegrasyonunun Python ekosistemindeki gücü göz önüne alınarak **Modular Monolith** mimarisi seçilmiştir. Bu yapı, mikroservislerin karmaşıklığını getirmeden modüllerin (Ingestion, Search, API) temiz bir şekilde ayrılmasını sağlar.

### Yüksek Seviye Katmanlar

1.  **Frontend (SPA):**
    *   **Teknoloji:** React (TypeScript), Tailwind CSS.
    *   **Rol:** Kullanıcı arayüzü, video oynatma, chatbot etkileşimi. Backend ile REST API üzerinden haberleşir.
2.  **API Gateway & Backend (Core):**
    *   **Teknoloji:** Python (FastAPI).
    *   **Rol:** Kimlik doğrulama, dosya yönetimi, klasörleme mantığı ve arama orkestrasyonu.
3.  **Asynchronous Workers (Ingestion Layer):**
    *   **Teknoloji:** Celery + Redis.
    *   **Rol:** Uzun süren video indirme, işleme (transcoding) ve AI analiz işlemlerini arka planda yönetir. API'nin bloklanmasını engeller.
4.  **AI & Intelligence Layer:**
    *   **Teknoloji:** LangChain / LlamaIndex.
    *   **Rol:** Video içeriğini anlama (Video-to-Text), Embedding üretme ve RAG (Retrieval-Augmented Generation) pipeline'ı.
5.  **Veri Katmanı (Data Layer):**
    *   **Metadata DB:** PostgreSQL (Kullanıcılar, Klasörler, Etiketler).
    *   **Vector Store:** pgvector (PostgreSQL eklentisi) veya Qdrant. (MVP için pgvector önerilir).
    *   **Object Storage:** AWS S3 veya MinIO (Fiziksel video dosyaları).

---

## 2. Bileşenler ve Sorumluluklar

### A. Video Ingestion (İçeri Alma Hattı)
Bu modül, dış dünyadan (Instagram, TikTok, YouTube) verinin sisteme giriş kapısıdır.
*   **Downloader:** `yt-dlp` kütüphanesi wrapper'ı. Link doğrulama ve en iyi kalitede indirme işlemini yapar.
*   **Normalizer:** İndirilen videoları standart bir formata (örn. MP4, h.264) dönüştürür ve thumbnail üretir.
*   **Duplicate Checker:** Dosya hash'i (SHA-256) kontrolü ile aynı videonun tekrar yüklenmesini engeller.

### B. Metadata & Tag Yönetimi
*   **CRUD Servisi:** Klasör hiyerarşisi ve etiketleme işlemlerini yönetir.
*   **Hybrid Tagging:** Hem kullanıcının manuel girdiği etiketleri hem de AI'ın önerdiği etiketleri birleştirir.

### C. AI Analiz ve Eşleştirme Motoru
Bu sistemin "beyni"dir. Videoları sadece dosya ismiyle değil, içeriğiyle anlar.
*   **Vision Analyzer:** Videonun kilit karelerini (keyframes) alır ve Multimodal LLM (örn. GPT-4o veya Gemini 1.5 Flash) kullanarak görseli metne döker.
    *   *Çıktı Örneği:* "Bir kedi masadan bardağı bilerek itiyor ve sahibi bağırıyor."
*   **Embedding Generator:** Üretilen metinsel açıklamayı ve etiketleri vektör uzayına (embeddings) dönüştürür (örn. `text-embedding-3-small`).

### D. Chatbot & Arama Katmanı (RAG)
*   **Intent Classifier:** Kullanıcının sorgusunun bir "arama" mı yoksa "sohbet" mi olduğunu anlar.
*   **Vector Search:** Kullanıcı sorgusunu vektöre çevirip veritabanındaki en yakın videoları bulur (Cosine Similarity).
*   **Response Synthesizer:** Bulunan videoların metadata'larını alıp kullanıcıya doğal dilde yanıt döner.
    *   *Örnek Yanıt:* "Aradığın 'gol yemeden atamazsın' videosunu 'Futbol Geyikleri' klasöründe buldum, işte burada:"

---

## 3. Veri Modeli (High-Level Schema)

İlişkisel veritabanı (PostgreSQL) üzerinde kurgulanacaktır.

### `Video` Tablosu
*   `id` (UUID): Benzersiz kimlik.
*   `source_url` (String): Orijinal link (Instagram vb.).
*   `s3_key` (String): Object storage yolu.
*   `file_hash` (String): Duplicate kontrolü için.
*   `description_manual` (Text): Kullanıcı notu.
*   `description_ai` (Text): AI tarafından üretilen sahne açıklaması.
*   `embedding` (Vector): `description_ai` + `tags` üzerinden oluşturulan vektör.
*   `duration` (Int): Saniye cinsinden süre.
*   `created_at` (Timestamp).

### `Folder` Tablosu
*   `id` (UUID).
*   `parent_id` (UUID, Nullable): Alt klasör yapısı için (Self-referencing).
*   `name` (String).
*   `user_id` (UUID): Klasör sahibi.

### `Tag` Tablosu
*   `id` (UUID).
*   `name` (String): (örn. "komik", "kedi", "futbol").
*   `type` (Enum): "MANUAL" veya "AI_GENERATED".

### `VideoTags` (Pivot Tablo)
*   Many-to-Many ilişkisi (`video_id` <-> `tag_id`).

---

## 4. AI Kullanım Stratejisi

Sistemin başarısı, videoyu ne kadar iyi "metne" dökebildiğine bağlıdır. Videoları doğrudan vektörleştirmek (Video Embeddings) maliyetli ve karmaşıktır. Bu yüzden **"Video-to-Text-to-Vector"** stratejisi izlenecektir.

### Pipeline Adımları:

1.  **Video -> Frame:** Videodan her 5-10 saniyede bir veya sahne geçişlerinde "keyframe" çıkarılır.
2.  **Frame -> Description (Captioning):**
    *   Model: Gemini 1.5 Flash (Hızlı, ucuz ve multimodal) veya GPT-4o-mini.
    *   Prompt: *"Bu videodaki komik olayı, karakterleri, varsa ekrandaki yazıları ve duygu durumunu detaylıca tasvir et."*
3.  **Description -> Embedding:**
    *   Elde edilen açıklama, video başlığı ve etiketler birleştirilir.
    *   OpenAI `text-embedding-3-small` ile vektör oluşturulur.
    *   Postgres `pgvector` kolonuna kaydedilir.

### Chatbot Sorgu Akışı:
1.  Kullanıcı: *"Hani şu 5 gol yemeden atamayan adam vardı ya"*
2.  Backend: Bu cümleyi aynı embedding modeli ile vektöre çevirir.
3.  DB: Vektör uzayında bu sorguya en yakın `description_ai` alanına sahip videoları getirir (Semantic Search).
4.  Reranking (Opsiyonel): Bulunan sonuçları kesinlik oranına göre sıralar.
5.  Chatbot: En yüksek skorlu videoyu kullanıcıya sunar.

---

## 5. Dosya & Klasör Yapısı (Backend Odaklı)

FastAPI için ölçeklenebilir, "Domain-Driven" esintili bir yapı önerilir.

```text
/backend
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── videos.py    # Video CRUD, Upload
│   │   │   │   ├── folders.py   # Klasör işlemleri
│   │   │   │   ├── chat.py      # Chatbot / Search endpoint
│   │   │   └── api.py
│   ├── core/
│   │   ├── config.py            # Env değişkenleri
│   │   ├── security.py          # JWT, Auth
│   │   └── db.py                # Database connection
│   ├── models/                  # SQLAlchemy / Pydantic modelleri
│   │   ├── video.py
│   │   ├── tag.py
│   │   └── user.py
│   ├── services/
│   │   ├── ingestion/
│   │   │   ├── downloader.py    # yt-dlp wrapper
│   │   │   └── processor.py     # FFMPEG işlemleri
│   │   ├── intelligence/
│   │   │   ├── captioning.py    # Vision LLM entegrasyonu
│   │   │   └── vectorizer.py    # Embedding yönetimi
│   │   └── storage.py           # S3 adaptörü
│   ├── workers/
│   │   └── tasks.py             # Celery task tanımları
│   └── main.py
├── alembic/                     # DB Migrations
├── docker-compose.yml
├── requirements.txt
├── .env.example   # .env buradan kopyalanır; .env repoya eklenmez
└── BLUEPRINT.md
```

---

## 6. Teknik Riskler ve Edge Case'ler

1.  **Platform Engelleri (Rate Limiting & Blocking):**
    *   *Risk:* Instagram/YouTube sık sık yapı değiştirir, downloader bozulabilir.
    *   *Çözüm:* `yt-dlp` kütüphanesini container restart'larında otomatik güncelleyen bir yapı kurmak. Proxy rotasyonu kullanmak.
2.  **Yanlış Eşleşme (Hallucination):**
    *   *Risk:* Kullanıcı "sarı kedi" arar, AI "sarı köpek" videosunu getirebilir çünkü embeddingleri yakındır.
    *   *Çözüm:* Vektör aramasına ek olarak metadata filtresi (Hybrid Search) kullanmak (örn. Tag='kedi' AND vector_similarity > 0.8).
3.  **Performans (Latency):**
    *   *Risk:* Video yükleme sırasında AI analizi uzun sürebilir.
    *   *Çözüm:* Kullanıcıya video yüklendiği anda "İşleniyor" statüsü göstermek, AI analizini asenkron (background) yapmak. Video hemen izlenebilir olsun, arama özelliği sonra aktifleşsin.
4.  **Depolama Maliyeti:**
    *   *Risk:* Videolar çok yer kaplar.
    *   *Çözüm:* Yükleme sırasında FFMPEG ile videoları optimize edilmiş bir bitrate/çözünürlüğe (örn. 720p Mobile) düşürmek (Transcoding).

---

## 7. MVP vs Gelişmiş Versiyon

### Faz 1: MVP (Minimum Viable Product)
*   **Temel Özellikler:**
    *   Instagram/TikTok linki yapıştır -> İndir -> S3'e kaydet.
    *   Otomatik Thumbnail üretimi.
    *   Klasörleme ve Manuel Etiketleme.
    *   **Basit AI:** Sadece videonun ilk karesini (thumbnail) alıp "Image Captioning" yapması ve buna göre arama yapılması.
    *   Chatbot yok, sadece "Akıllı Arama Çubuğu".

### Faz 2: Gelişmiş Versiyon (Production)
*   **Gelişmiş AI:** Videoyu sahne sahne analiz eden (Video Understanding) modeller.
*   **Ses Analizi (Whisper):** Videodaki konuşmaların metne dökülmesi (Subtitle extraction) ve bu metin içinde arama yapılması (Full-text search).
*   **Chatbot:** "Bana güldürecek bir şeyler öner" gibi soyut istekleri karşılayan Persona.
*   **Sosyal Özellikler:** Arşivi başkasıyla paylaşma, ortak klasörler.
*   **Browser Extension:** Tarayıcıdayken sağ tık -> "MemeVault'a Kaydet".
