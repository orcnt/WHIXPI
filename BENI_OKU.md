# WHIXPI v1.0

<div align="center">

**Profesyonel Video & Ses Transkripsiyon Stüdyosu**

[![Lisans: Unlicense](https://img.shields.io/badge/Lisans-Unlicense-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg)](https://python.org)
[![CUDA 11.8+](https://img.shields.io/badge/CUDA-11.8+-76B900.svg)](https://developer.nvidia.com/cuda-toolkit)

*Geliştirici: Alparslan Orçun Tarhan*

</div>

---

## Proje Hakkında

WHIXPI, video ve ses dosyalarınızı milisaniye hassasiyetinde metne dönüştüren ve profesyonel altyazılar (SRT, JSON, TXT) oluşturan bir masaüstü uygulamasıdır.

Arka planda OpenAI'ın Whisper modelini (konuşma tanıma), Meta'nın Wav2Vec2 modelini (kelime-ses hizalama) ve Silero VAD'ı (ses-sessizlik ayrımı) kullanır. Bunların üzerine eklenen özel algoritmalar — **Miller Hybrid Splitter** (altyazı bölümleme) ve **Chronos Timing Engine** (zamanlama iyileştirme) — çıktıyı profesyonel seviyeye taşır.

**Hedef kullanıcılar:** Sosyal medya içerik üreticileri, altyazı çevirmenleri, transkripsiyon uzmanları ve veri analistleri.

---

## Sürümler

### Taşınabilir Sürüm (Önerilen)
Hiçbir kurulum gerektirmez. İçerisinde Whisper Large-v3 modeli ve FFmpeg araçları hazır olarak gelir.

- **Dosya:** `WHIXPI_v1.0_Final_Portable.zip`
- **Kullanım:** ZIP dosyasını açın → `WHIXPI.exe` dosyasını çalıştırın.
- **Boyut:** ~6 GB (yapay zeka modeli dahil)

### Kaynak Kod Sürümü (Geliştiriciler İçin)
Doğrudan Python ortamında çalıştırma.

1. **Python 3.10+** yüklü olduğundan emin olun.
2. [PyTorch'u CUDA desteğiyle kurun](https://pytorch.org/get-started/locally/).
3. [WhisperX'i kurun](https://github.com/m-bain/whisperx).
4. Kalan bağımlılıkları kurun: `pip install -r requirements.txt`
5. Çalıştırın: `python main.py`

Detaylı kurulum adımları için [Gereksinimler](#gereksinimler) bölümüne bakın.

---

## Özellikler

### Yapay Zeka Motoru
- **Whisper Large-v3** — OpenAI'ın en güçlü açık kaynaklı konuşma tanıma modeli
- **Wav2Vec2 Hizalama** — Kelime düzeyinde milisaniye hassasiyetinde zaman damgası eşleştirme
- **Silero VAD** — Konuşma başlangıcı ve bitişini cerrahi hassasiyetle tespit eden akıllı ses analizi
- **Diamond Precision** — VAD destekli başlangıç/bitiş zamanlarının hassas iyileştirmesi

### Özel Algoritmalar
- **Miller Hybrid Splitter** — Dengeli ve estetik altyazı bölümleme. Satır dengeleme, bağlaç koruması ve tek kelime sarkmalarını önleme mantığı içerir
- **Chronos Timing Engine** — Kelimeler ve cümleler arasındaki boşlukları akıllıca köprüleyen ve zamanlamaları dinamik olarak dağıtan motor

### Çıktı Formatları

| Format | Kullanım Alanı |
|:---|:---|
| SRT (Kelime bazlı) | YouTube Shorts, Instagram Reels, TikTok |
| SRT (Cümle bazlı) | Film altyazıları, belgeseller, uzun videolar |
| JSON (Ham veri) | Programatik işleme, veri analizi, otomasyon |
| TXT (Düz metin) | Metin editörleri, arama, arşivleme |
| TXT (Zamanlı) | Detaylı log dosyaları, manuel inceleme |

### Performans Profilleri (VRAM Yönetimi)

| Profil | VRAM Kullanımı | Batch | Beam | Önerilen Ekran Kartı |
|:---|:---|:---|:---|:---|
| SONIC | 13–14 GB | 32 | 1–5 | RTX 4090 / 3090 |
| ULTRA | ~12 GB | 10 | 20 | RTX 4080 / 3080 |
| YÜKSEK | ~10 GB | 10 | 10 | RTX 4070 / 3070 |
| DENGELİ | ~6 GB | 6 | 5 | RTX 4060 / 3060 |
| EKO | 3–4 GB | 1 | 1 | GTX 1650 / 1060 |
| DENEYSEL | Özel | Özel | Özel | Sadece ileri düzey kullanıcılar |

### Arayüz
- Koyu / Açık tema desteği
- Türkçe ve İngilizce arayüz dili
- Yüksek DPI uyumluluğu (4K ekran desteği)
- Win32 API üzerinden yerel Windows Sürükle-Bırak desteği

---

## Proje Yapısı

```
WHIXPI/
├── main.py                 # Uygulama giriş noktası
├── Baslat.bat              # Hızlı başlatma betiği (Windows)
├── requirements.txt        # Python bağımlılıkları
├── settings.json           # Kullanıcı ayarları (otomatik oluşturulur)
│
├── src/
│   ├── engine/
│   │   ├── logic.py        # Miller Hybrid Splitter & Chronos Timing
│   │   └── worker.py       # AI Transkripsiyon İşçisi (multiprocessing)
│   ├── ui/
│   │   ├── main_window.py  # Ana uygulama penceresi
│   │   ├── dialogs.py      # Özel diyalog pencereleri
│   │   └── styles.py       # Tema tanımları ve renk paletleri
│   └── utils/
│       └── helpers.py      # DPI, Sürükle-Bırak, yol çözümleme, yerelleştirme
│
├── locales/
│   ├── tr.json             # Türkçe çeviriler
│   └── en.json             # İngilizce çeviriler
│
├── resources/
│   ├── icon.ico            # Uygulama ikonu
│   └── logo.png            # Uygulama logosu
│
├── models/                 # Yapay zeka model dizini (otomatik indirilir)
│   └── large-v3/           # Whisper Large-v3 model dosyaları
│
└── bin/                    # Harici araçlar
    ├── ffmpeg.exe          # Medya işleme
    └── ffprobe.exe         # Medya bilgisi
```

---

## Gereksinimler

### Sistem Gereksinimleri
- **İşletim Sistemi:** Windows 10/11 (64-bit)
- **RAM:** En az 8 GB (16 GB önerilir)
- **Ekran Kartı:** NVIDIA GPU, 4 GB+ VRAM (CUDA 11.8+)
- **Disk:** ~10 GB boş alan (model + uygulama)

### Python Bağımlılıkları (Kaynak Kod Sürümü)

**Adım 1: PyTorch Kurulumu (CUDA 11.8)**
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Adım 2: WhisperX Kurulumu**
```bash
pip install git+https://github.com/m-bain/whisperx.git
```

**Adım 3: Diğer Bağımlılıkların Kurulumu**
```bash
pip install -r requirements.txt
```

`requirements.txt` şunları içerir: `customtkinter`, `Pillow`, `numpy`, `scipy`, `transformers`, `ffmpeg-python`.

**Not:** Whisper Large-v3 modeli (~3.1 GB), ilk çalıştırmada otomatik olarak `models/` dizinine indirilir.

---

## Nasıl Kullanılır

1. **Dosya Ekleyin** — "+ DOSYA EKLE" butonuna tıklayın veya dosyaları doğrudan pencereye sürükleyip bırakın.
2. **Format Seçin** — İhtiyacınıza göre çıktı formatlarını seçin (SRT, JSON, TXT).
3. **Yapılandırın** — Ayarlar ve Performans sekmelerinden VRAM profili, köprüleme eşikleri ve altyazı limitlerini ayarlayın.
4. **Başlatın** — BAŞLAT butonuna basın. Transkripsiyon arka plan sürecinde çalışır, arayüz donmaz.
5. **Sonuçlar** — Çıktı dosyaları seçtiğiniz çıktı klasörüne kaydedilir.

---

## Geliştirme

### Yeni Dil Eklemek
1. `locales/` klasörüne yeni bir JSON dosyası ekleyin (örn: Almanca için `de.json`).
2. `tr.json` dosyasındaki tüm anahtarları kopyalayıp değerleri yeni dile çevirin.
3. Uygulama yeni dili otomatik olarak algılayacaktır.

### Tema Özelleştirme
`src/ui/styles.py` dosyasındaki `THEMES` sözlüğünü düzenleyerek yeni renk paletleri ekleyebilir veya mevcut temaları değiştirebilirsiniz.

---

## Üçüncü Taraf Bileşenler ve Lisansları

WHIXPI, aşağıda listenen açık kaynaklı projeler üzerine inşa edilmiştir. Her projenin telif hakkı kendi yazar ve katkıda bulunanlarına aittir.

**WHIXPI'yi yeniden dağıtan veya değiştiren kişiler, bu üçüncü taraf bileşenlerin lisanslarına uymak zorundadır.**

| Bileşen | Lisans | Yazar / Kuruluş | Bağlantı |
|:---|:---|:---|:---|
| OpenAI Whisper | MIT | OpenAI | [github.com/openai/whisper](https://github.com/openai/whisper) |
| WhisperX | BSD-4-Clause | Max Bain | [github.com/m-bain/whisperx](https://github.com/m-bain/whisperx) |
| Faster-Whisper | MIT | SYSTRAN / Guillaume Klein | [github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| CTranslate2 | MIT | OpenNMT | [github.com/OpenNMT/CTranslate2](https://github.com/OpenNMT/CTranslate2) |
| Silero VAD | MIT | snakers4 | [github.com/snakers4/silero-vad](https://github.com/snakers4/silero-vad) |
| PyTorch | BSD-3-Clause | Meta / Facebook AI Research | [pytorch.org](https://pytorch.org/) |
| Transformers | Apache-2.0 | Hugging Face | [github.com/huggingface/transformers](https://github.com/huggingface/transformers) |
| Hugging Face Hub | Apache-2.0 | Hugging Face | [github.com/huggingface/huggingface_hub](https://github.com/huggingface/huggingface_hub) |
| SpeechBrain | Apache-2.0 | SpeechBrain Ekibi | [github.com/speechbrain/speechbrain](https://github.com/speechbrain/speechbrain) |
| Wav2Vec2 XLS-R Türkçe | CC BY-NC 4.0* | Özcan Gündeş | [huggingface.co/ozcangundes](https://huggingface.co/ozcangundes/wav2vec2-large-xlsr-53-turkish) |
| FFmpeg | LGPL-2.1+ / GPL | FFmpeg Ekibi | [ffmpeg.org](https://ffmpeg.org/) |
| CustomTkinter | MIT | Tom Schimansky | [github.com/TomSchimansky/CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Pillow (PIL) | HPND | Jeffrey A. Clark (Alex) | [github.com/python-pillow/Pillow](https://github.com/python-pillow/Pillow) |
| NumPy | BSD-3-Clause | NumPy Geliştiricileri | [numpy.org](https://numpy.org/) |
| SciPy | BSD-3-Clause | SciPy Geliştiricileri | [scipy.org](https://scipy.org/) |
| ffmpeg-python | Apache-2.0 | Karl Kroening | [github.com/kkroening/ffmpeg-python](https://github.com/kkroening/ffmpeg-python) |

### FFmpeg Hakkında Önemli Not

FFmpeg, derlenmiş ikili dosya olarak (`bin/ffmpeg.exe` ve `bin/ffprobe.exe`) **LGPL-2.1+** (veya derleme yapılandırmasına bağlı olarak GPL) lisansı koşullarında dağıtılmaktadır. WHIXPI, FFmpeg kaynak kodunu değiştirmez; medya işleme için harici bir araç olarak kullanır.

FFmpeg kaynak kodu: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### Wav2Vec2 Türkçe Modeli Hakkında Önemli Not

Türkçe hizalama modeli (`ozcangundes/wav2vec2-large-xlsr-53-turkish`), model kartına bağlı olarak **CC BY-NC 4.0** lisansına tabi olabilir. Bu, modelin ticari olmayan kullanımla sınırlı olabileceği anlamına gelir. WHIXPI'yi ticari amaçlarla kullanmayı planlıyorsanız, bu modelin lisans koşullarını doğrulayın veya alternatif bir hizalama modeli kullanın.

---

## Lisans

Bu projenin kendi kodu **[The Unlicense](LICENSE)** kapsamında kamu malı (public domain) olarak yayınlanmıştır.

Bu yazılımı herhangi bir amaçla — ticari veya ticari olmayan — kopyalayabilir, değiştirebilir, yayımlayabilir, kullanabilir, derleyebilir, satabilir veya dağıtabilirsiniz.

Orijinal geliştiriciye (**Alparslan Orçun Tarhan**) bir teşekkür notu eklemek takdir edilir, ancak zorunlu değildir.

**Ancak**, WHIXPI ile birlikte paketlenen veya kullanılan üçüncü taraf bileşenlerin kendi lisanslarına tabi olduğunu unutmayın (yukarıdaki tabloya bakın). Yeniden dağıtım yaparken bu lisanslara uymanız gerekmektedir.

---

<div align="center">

*Her sesin bir metni, her metnin bir zamanı vardır.*

</div>
