# Mimari Kararlar (ADR)

Bu belge, MemeVault projesinde BLUEPRINT.md’ye dayalı alınan mimari kararları özetler.

---

## ADR-001: Modular Monolith (Python/FastAPI)

**Bağlam:** Ölçeklenebilirlik, bakım kolaylığı ve AI entegrasyonu ihtiyacı.

**Karar:** Backend, Modular Monolith olarak kalacak; modüller (Ingestion, Search, API, Intelligence) aynı uygulama içinde ayrı paketler halinde organize edilecek. Mikroservise geçiş şimdiki kapsamda yok.

**Sonuçlar:** Tek deploy, tek veritabanı, net modül sınırları; ileride modüller ayrı servislere bölünebilir.

---

## ADR-002: Event-Driven Ingestion (Celery + Redis)

**Bağlam:** Uzun süren indirme, transcoding ve AI analizi API’yi bloklamamalı.

**Karar:** İçeri alma (download → normalizer → duplicate check → S3 → AI caption → embedding) Celery task’ları ile asenkron yapılacak. Redis broker kullanılacak.

**Sonuçlar:** Kullanıcı videoyu hemen “yüklendi” görür; arama özelliği işlem tamamlanınca devreye girer. API yanıt süreleri kısa kalır.

---

## ADR-003: Video–Text–Vector Stratejisi (MVP)

**Bağlam:** Videoyu doğrudan vektörleştirmek maliyetli ve karmaşık.

**Karar:** MVP’de “Video → (tek) Keyframe/Thumbnail → Image Captioning → Metin + Etiketler → Embedding → pgvector” pipeline’ı kullanılacak. Tam video/sahne analizi Faz 2’ye bırakılacak.

**Sonuçlar:** Daha düşük maliyet, daha hızlı işlem; arama kalitesi MVP için yeterli kabul edilir.

---

## ADR-004: Vector Store olarak pgvector

**Bağlam:** BLUEPRINT’te pgvector ve Qdrant seçenekleri var.

**Karar:** MVP’de vektörler PostgreSQL içinde pgvector ile saklanacak. Ayrı bir Qdrant sunucusu kurulmayacak.

**Sonuçlar:** Tek veritabanı, daha az operasyonel yük; büyük ölçekte Qdrant’a geçiş mümkün.

---

## ADR-005: MVP Kapsamı – Chatbot Yok, Akıllı Arama Var

**Bağlam:** BLUEPRINT’te hem “Chatbot” hem “sadece Akıllı Arama Çubuğu” (MVP) tanımlı.

**Karar:** İlk teslimde sadece “Akıllı Arama” endpoint’i sunulacak: metin sorgusu → embedding → vector search → video listesi. Intent classifier ve sohbet persona Faz 2’de eklenecek.

**Sonuçlar:** Daha basit API ve test; kullanıcı “arama çubuğu” ile semantik arama yapabilir.

---

## ADR-006: Kimlik Doğrulama – JWT

**Bağlam:** API Gateway’de “kimlik doğrulama” gereksinimi var; detay BLUEPRINT’te yok.

**Karar:** Kimlik doğrulama JWT (access token) ile yapılacak; `core/security.py` içinde token üretimi ve doğrulama yer alacak. Kullanıcı kaydı/girişi için User modeli kullanılacak.

**Sonuçlar:** Stateless API; frontend token’ı saklayıp isteklerde gönderir.

---

## ADR-007: Object Storage – S3 Uyumlu Arayüz (MinIO Destekli)

**Bağlam:** Fiziksel video dosyaları için “AWS S3 veya MinIO” denmiş.

**Karar:** Kod, S3 uyumlu bir arayüz (boto3 veya minio-py) kullanacak; geliştirme ortamında MinIO, production’da AWS S3 kullanılabilir. Konfigürasyon ile seçilecek.

**Sonuçlar:** Yerel ve bulut ortamlarında aynı kod kullanılır.

---

## ADR-008: Hybrid Search (Vector + Metadata) Riski Azaltma

**Bağlam:** BLUEPRINT’te “yanlış eşleşme” riski için Hybrid Search (tag + vector_similarity) önerilmiş.

**Karar:** Arama API’sinde isteğe bağlı tag/klasör filtresi desteklenecek; vektör benzerliği eşiği (örn. 0.8) konfigüre edilebilecek. MVP’de basit vector search + opsiyonel tag filtresi yeterli.

**Sonuçlar:** Daha isabetli sonuçlar; ileride reranking eklenebilir.

---

*Bu kararlar BLUEPRINT.md 1.0.0 ve docs/EKSIK_VE_CELISKILER.md ile uyumludur.*
