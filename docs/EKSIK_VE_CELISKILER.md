# BLUEPRINT Eksik ve Çelişkili Noktalar Raporu

Bu belge, BLUEPRINT.md'ye göre geliştirme yaparken tespit edilen eksiklikleri ve çözüm kararlarını içerir.

---

## 1. Eksiklikler

### 1.1 User Tablosu Tanımı
- **Durum:** Veri modeli bölümünde `User` tablosu açıkça tanımlanmamış; sadece `Folder.user_id` ile referans verilmiş.
- **Karar:** `User` tablosu eklendi: `id` (UUID), `email`, `hashed_password`, `created_at`. Kimlik doğrulama (JWT) için gerekli.

### 1.2 Video–Folder İlişkisi
- **Durum:** Şemada bir videonun hangi klasör(ler)e ait olduğu belirtilmemiş.
- **Karar:** MVP için bir videonun tek bir klasörde olması yeterli. `Video` tablosuna `folder_id` (UUID, nullable) alanı eklendi.

### 1.3 Duplicate Checker Konumu
- **Durum:** Bileşenlerde "Duplicate Checker" geçiyor; dosya yapısında ayrı bir modül yok.
- **Karar:** Duplicate kontrolü `services/ingestion/processor.py` içinde (veya `downloader.py` sonrası tek bir pipeline adımı olarak) `file_hash` ile yapılacak; ayrı dosya açılmadı.

### 1.4 RAG / Chat Katmanı Servis Konumu
- **Durum:** Intent Classifier, Vector Search, Response Synthesizer tanımlı; klasör yapısında sadece `endpoints/chat.py` var.
- **Karar:** Bu mantık `services/intelligence/` altında tutulacak: vector search için `vectorizer.py` (veya ayrı `search.py`), intent + response için `chat.py` veya `rag.py` servis dosyası eklendi. MVP’de sadece “Akıllı Arama Çubuğu” olduğu için tam chatbot yerine önce arama odaklı endpoint yazılacak.

### 1.5 models/folder.py
- **Durum:** BLUEPRINT’te `models/` altında sadece `video.py`, `tag.py`, `user.py` sayılmış; `Folder` tablosu var.
- **Karar:** `models/folder.py` eklendi; Folder modeli burada tanımlanacak.

---

## 2. Çelişkiler / Belirsizlikler

### 2.1 MVP vs Gelişmiş Sürüm
- **Durum:** Hem “Faz 1: MVP” (thumbnail captioning, chatbot yok, sadece akıllı arama) hem “Faz 2” (chatbot, sahne analizi) anlatılmış.
- **Karar:** İlk geliştirme **MVP (Faz 1)** ile sınırlı: tek keyframe/thumbnail ile image captioning, sadece arama endpoint’i. Chatbot ve gelişmiş video analizi sonraki fazda eklenecek.

### 2.2 Vector Store Konumu
- **Durum:** “pgvector veya Qdrant” denmiş; “MVP için pgvector önerilir” denmiş.
- **Karar:** MVP’de **pgvector** kullanılacak; embedding `Video` tablosunda veya ilişkili tek bir vektör tablosunda tutulacak.

### 2.3 LangChain / LlamaIndex
- **Durum:** Katmanda “LangChain / LlamaIndex” yazıyor; pipeline adımlarında doğrudan model isimleri (Gemini, OpenAI) geçiyor.
- **Karar:** MVP’de framework bağımlılığı minimize edilecek: doğrudan API çağrıları (OpenAI, Gemini) ile captioning ve embedding; ileride gerekirse LangChain/LlamaIndex eklenebilir.

---

## 3. Özet

| Konu              | Eksik/Çelişki | Alınan Karar                          |
|-------------------|---------------|----------------------------------------|
| User tablosu      | Eksik         | User modeli eklendi                    |
| Video–Folder      | Eksik         | Video.folder_id eklendi                |
| Duplicate Checker | Eksik         | Processor pipeline içinde              |
| RAG servis yeri   | Eksik         | services/intelligence/ altında        |
| models/folder.py  | Eksik         | folder.py eklendi                      |
| MVP kapsamı       | Belirsiz      | Sadece Faz 1 (MVP) uygulanacak         |
| Vector store      | Seçenek       | pgvector kullanılacak                  |
| LLM framework     | Seçenek       | MVP’de doğrudan API; framework opsiyonel |

Bu kararlar `docs/ARCHITECTURE_DECISIONS.md` ile uyumludur.
