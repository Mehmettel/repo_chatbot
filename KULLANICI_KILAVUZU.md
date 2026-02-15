# MemeVault — Kullanıcı Kılavuzu

**AI destekli video arşivi.** YouTube, Instagram, TikTok gibi platformlardan videoları ekleyin; anlam bazlı akıllı arama ile anında bulun.

---

## MemeVault Nedir?

MemeVault, video linklerini toplayıp **içeriklerine göre arayabildiğiniz** kişisel bir video arşividir. Örneğin:

- *"Maça girmeye hazırlanan adam"*
- *"Komedi sahnesi"*
- *"Recep İvedik"*

gibi cümlelerle videoları bulabilirsiniz. Sistem, videoları AI ile analiz eder (görüntü, ses, başlık) ve anlam bazlı arama yapar.

---

## Özellikler

| Özellik | Açıklama |
|---------|----------|
| **Video Ekleme** | Tek link, toplu URL listesi veya YouTube playlist ile video ekleyin |
| **Klasörler** | Videoları klasörlere ayırın (örn. "Komediler", "Spor") |
| **Akıllı Arama** | Doğal dil ile arayın; kelime kelime eşleşme gerekmez |
| **Video Başlığı** | Kaynak platformdan otomatik başlık alınır |
| **Ses Transkripti** | Videodaki konuşmalar metne çevrilir (Whisper AI) |
| **Görsel Analiz** | Videodan birden fazla kare analiz edilir (GPT-4o) |
| **Hybrid Arama** | Hem anlam hem anahtar kelime ile arama |

---

## Nasıl Kullanılır?

### 1. Giriş Yapın

- **İlk kullanım:** Ana sayfada "Kayıt Ol" ile e-posta ve şifre ile hesap oluşturun.
- **Sonraki girişler:** "Giriş Yap" ile giriş yapın.

### 2. Klasör Oluşturun

- Sol menüde **"+"** ile yeni klasör ekleyin.
- Örn: "Komediler", "Spor Videoları", "Recep İvedik".

### 3. Video Ekleyin

**Video Ekle** butonuna tıklayın. Üç mod vardır:

| Mod | Ne zaman kullanılır? | Nasıl? |
|-----|----------------------|--------|
| **Tek Video** | Tek bir link eklemek için | URL yapıştırın → Klasör seçin → Ekle |
| **Toplu URL** | Birden fazla link eklemek için | Her satıra bir URL veya virgülle ayırarak yazın → Toplu Ekle |
| **Playlist** | YouTube playlist eklemek için | Playlist linkini yapıştırın → Maksimum video sayısını seçin (1–100) → Toplu Ekle |

**Desteklenen platformlar:** YouTube, YouTube Shorts, Instagram, TikTok ve yt-dlp’nin desteklediği diğer siteler.

### 4. Video İşlenmesini Bekleyin

- **Bekliyor:** Kuyruğa alındı.
- **İşleniyor:** İndiriliyor, analiz ediliyor.
- **Tamamlandı:** İzlenebilir ve aranabilir.
- **Başarısız:** "Yeniden Dene" ile tekrar deneyebilirsiniz.

İşlem genelde video başına 30 saniye–2 dakika sürer.

### 5. Arama Yapın

- Üstteki arama çubuğuna **doğal dil** ile yazın.
- Örn: *"komik kediler"*, *"futbol maçı"*, *"stand-up gösterisi"*.
- Enter’a basın veya arama ikonuna tıklayın.
- Sonuçlar **benzerlik skoruna** göre sıralanır.

### 6. Videoyu İzleyin

- Video kartına tıklayın.
- Açılan pencerede:
  - Video oynatıcı
  - Video başlığı
  - AI görsel analizi
  - Ses transkripti (varsa)
  - İndir / Yeni sekmede aç

### 7. Video Yönetimi

- **3 nokta menüsü** (sağ üst): Taşı, Sil.
- **Sağ tık:** Aynı menü.
- **Yeniden Dene:** İşlem başarısız olan veya takılan videoları tekrar kuyruğa almak için.

---

## Sık Sorulan Sorular

**S: Örnek hesapla (deneme@gmail.com / deneme) giriş yapamıyorum.**  
C: Veritabanı sıfırlanmış olabilir (Docker yeniden oluşturulduğunda). API her başlatıldığında örnek kullanıcı otomatik oluşturulur. Docker ve backend çalışıyorsa sayfayı yenileyip tekrar deneyin. Manuel oluşturmak için: `cd backend` → `python -m app.seed_user`

**S: Video ekledim ama "Bekliyor"da kaldı.**  
C: Celery worker çalışıyor olmalı. Backend ile birlikte ayrı bir terminalde `celery -A app.workers.celery_app worker` komutunu çalıştırın.

**S: Arama sonuç vermiyor.**  
C: Videoların işlenmesi tamamlanmış olmalı (yeşil "Tamamlandı" rozeti). En az bir tamamlanmış video olmalı.

**S: Başlık veya transkript görünmüyor.**  
C: Yeni eklenen videolarda otomatik gelir. Eski videolar için ilgili videoda "Yeniden Dene" ile tekrar işlem tetikleyebilirsiniz.

**S: Playlist’ten kaç video eklenir?**  
C: Varsayılan 50, en fazla 100. Playlist modunda "Maksimum video sayısı" alanından değiştirebilirsiniz.

---

## Teknik Gereksinimler (Yerel Kurulum)

- **Docker Desktop** (PostgreSQL, Redis, MinIO için)
- **Python 3.11+** (backend)
- **Node.js 18+** (frontend)
- **FFmpeg** (video işleme)
- **OpenAI API anahtarı** (AI özellikleri için)

Detaylı kurulum için [README.md](README.md) ve `START.bat` (Windows) dosyasına bakın. Proje: [GitHub — repo_chatbot](https://github.com/Mehmettel/repo_chatbot).

---

## Özet

MemeVault ile:

1. Video linklerini toplu veya tek tek ekleyin.
2. Klasörlerle düzenleyin.
3. Doğal dil ile arayın.
4. Videoları izleyin, indirin ve yönetin.

**Tarayıcı adresi:** http://localhost:5173 (yerel kurulumda)
