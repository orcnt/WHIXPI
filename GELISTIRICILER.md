# WHIXPI v1.0 — Geliştirici Rehberi

> Bu rehber, WHIXPI'yi anlamak, değiştirmek veya üzerine inşa etmek isteyen geliştiriciler içindir.

---

## Yapay Zeka Boru Hattı Nasıl Çalışır

Kullanıcı "BAŞLAT" butonuna bastığında, aşağıdaki 4 adımlı süreç **ayrı bir işlemde** çalışır (böylece arayüz asla donmaz):

```
┌─────────────────────────────────────────────────────────┐
│  Adım 1: TRANSKRİPSİYON (worker.py)                    │
│  Whisper Large-v3 sesi metne çevirir.                   │
│  Girdi:  ses/video dosyası (.mp4, .wav vb.)             │
│  Çıktı:  yaklaşık zaman damgalı ham segmentler          │
├─────────────────────────────────────────────────────────┤
│  Adım 2: HİZALAMA (worker.py)                          │
│  Wav2Vec2 her kelimeyi ses dalgasıyla eşleştirir.       │
│  Girdi:  Adım 1'den gelen ham segmentler                │
│  Çıktı:  kelime düzeyinde zaman damgaları (ms hassas.)  │
├─────────────────────────────────────────────────────────┤
│  Adım 3: DIAMOND RAFİNERİ + CHRONOS (worker.py)        │
│  Silero VAD ile başlangıç/bitiş zamanları rafine edilir │
│  Chronos ile kelime/cümle arası boşluklar köprülenir    │
│  Girdi:  Adım 2'den gelen hizalanmış segmentler        │
│  Çıktı:  iyileştirilmiş zaman damgaları                │
├─────────────────────────────────────────────────────────┤
│  Adım 4: MILLER HİBRİT BÖLÜMLEME (logic.py)            │
│  Metin, dengeli altyazı bloklarına bölünür              │
│  Girdi:  Adım 3'ten gelen rafine segmentler             │
│  Çıktı:  nihai SRT/JSON/TXT dosyaları                   │
└─────────────────────────────────────────────────────────┘
```

---

## Dosya Haritası

### `main.py` — Giriş Noktası
- DPI farkındalığı, çoklu işlem desteği ve gereksiz log bastırmayı ayarlar.
- `WhisperXApp().mainloop()` çağrısıyla arayüzü başlatır.
- Programın ilk çalışan dosyasıdır.

### `src/engine/worker.py` — Beyin
- **En önemli dosya.** Tüm yapay zeka boru hattını içerir.
- `multiprocessing.Process` olarak çalışır, böylece arayüz donmaz.
- Model yükleme, transkripsiyon, hizalama ve VAD iyileştirme işlemlerini yönetir.
- Arayüzle `log_q` (log mesajları) ve `result_q` (sonuçlar) kuyrukları üzerinden iletişim kurar.

**Önemli fonksiyonlar:**
- `run()` — Ana boru hattı yöneticisi. 4 adımı sırayla çalıştırır.
- `diamond_refinery()` — VAD tabanlı zaman damgası iyileştirme. Silero VAD modeli ile konuşmanın gerçek başlangıç ve bitişini tespit eder.
- `analyze_vad_params()` — Ses dosyasının karakteristiğine göre VAD hassasiyetini otomatik ayarlar (gürültü analizi yapar).
- `get_vad_model()` — Silero VAD modelini yükler ve önbelleğe alır (tekrar tekrar yüklememek için).

### `src/engine/logic.py` — Özel Algoritmalar
WHIXPI'nin çıktısını benzersiz kılan iki imza algoritmasını içerir:

- **`miller_hybrid_split()`** — Metni dengeli altyazı bloklarına böler.
  - Satır dengeleme: İki satırlı altyazılarda satırları eşit uzunlukta tutar.
  - Bağlaç koruması: "ve", "ama", "çünkü" gibi kelimeler satır sonunda kalmaz, alt satıra atılır.
  - Anti-sarkma: Tek bir kelime alt satıra sarkmaz, üst satırdan bir kelime daha indirilir.
  - Karakter/kelime/satır limitlerini uygular.

- **`chronos_seamless_core()`** — Segmentler arası boşlukları köprüler.
  İki segment arasındaki boşluk eşik değerinden küçükse, boşluğu kapatır. Ayrıca örtüşmeleri düzeltir ve minimum süreyi garantiler.

- **`waveform_finetune_chronos()`** — Kelimeler arası mikro-boşlukları dinamik olarak dağıtır.

### `src/ui/main_window.py` — Yüz (Arayüz)
- Ana uygulama penceresi. Tüm arayüz mantığını içerir.
- Sekme yönetimi (Transkripsiyon, Ayarlar, Performans).
- Dosya kuyruğu yönetimi, ayar kaydetme/yükleme, tema değiştirme.
- Windows Sürükle-Bırak kancası kurulumu.
- VRAM profili değişiklik mantığı (Sonic, Ultra, Eko vb.).

### `src/ui/styles.py` — Renkler ve Fontlar
- `THEMES` sözlüğü: Koyu ve Açık renk paletleri. Her tema aynı anahtar yapısını kullanır.
- `FONTS` sözlüğü: Font tanımları (başlık, gövde, monospace vb.).
- `SIZES` sözlüğü: Pencere ve bileşen boyutları.
- **Yeni tema eklemek için:** `THEMES` sözlüğüne aynı renk anahtarlarıyla yeni bir giriş ekleyin.

### `src/ui/dialogs.py` — Açılır Pencereler
- `CustomNamingDialog`: Kullanıcının çıktı dosyalarını manuel adlandırmasını sağlar.
- `ProgressDialog`: İlerleme göstergesi.
- `ConfirmDialog`: Evet/Hayır onay penceresi.

### `src/utils/helpers.py` — Yardımcı Araçlar
- `get_resource_path()`: İkon ve logo dosyalarını bulur. Hem normal Python hem EXE modunda çalışır. Önce EXE'nin yanına, sonra `_internal` klasörüne bakar.
- `LocaleManager`: JSON tabanlı çeviri sistemi. Dil dosyalarını yükler ve `get(anahtar)` ile çeviri döndürür.
- `enable_high_dpi_awareness()`: Windows'ta yüksek çözünürlüklü ekranlarda bulanıklığı önler.
- Windows Sürükle-Bırak: Win32 API kancaları ile doğrudan dosya sürükleme desteği.

### `locales/tr.json` ve `en.json` — Çeviriler
- Her arayüz metni bir anahtar-değer çiftidir. Örnek: `"start_btn": "BAŞLAT"`
- **Yeni dil eklemek için:** `tr.json` dosyasını kopyalayın, `xx.json` olarak adlandırın, değerleri çevirin. Uygulama otomatik algılar.

---

## Sık Yapılan Değişiklikler

### "Yapay zeka modelini değiştirmek istiyorum"
```python
# worker.py, ~satır 235
model = whisperx.load_model(
    "large-v3",  # Bunu "medium", "small", "large-v3-turbo" vb. ile değiştirin
    device,
    compute_type=compute_type,
    ...
)
```

### "Yeni bir VRAM profili eklemek istiyorum"
```python
# worker.py, v_map sözlüğü (~satır 121)
# Format: "profil_adi": (batch_boyutu, beam_boyutu, "hesaplama_tipi")
v_map = {
    "vram_sonic": (32, 1, "float16"),
    "vram_benim_profilim": (16, 10, "float16"),  # Yeni profilinizi buraya ekleyin
    ...
}
# Sonra main_window.py dosyasındaki setup_perf_tab() fonksiyonuna
# eşleşen bir RadioButton ekleyin.
```

### "Altyazı bölümleme kurallarını değiştirmek istiyorum"
```python
# logic.py, miller_hybrid_split() fonksiyonu
# Önemli değişkenler:
#   mw = altyazı bloğu başına maksimum kelime sayısı (0 = sınırsız)
#   ml = altyazı bloğu başına maksimum satır sayısı (0 = sınırsız)
#   base_l = satır başına maksimum karakter sayısı
#   conjunctions = satır sonunda kalmaması gereken bağlaçlar listesi
```

### "Yeni bir çıktı formatı eklemek istiyorum"
```python
# main_window.py dosyasında SRT/JSON/TXT dosyalarının yazıldığı
# bölümü bulun ("write" veya "save" aratarak).
# Kendi format mantığınızı oraya ekleyin.
```

### "Türkçe hizalama modelini değiştirmek istiyorum"
```python
# worker.py, ~satır 277
align_model_name = (
    "ozcangundes/wav2vec2-large-xlsr-53-turkish"  # Bunu değiştirin
    if self.lang == "tr" else None
)
# Alternatifler:
# "facebook/wav2vec2-large-xlsr-53" (Genel model, daha geniş eğitim seti)
# "jonatasgrosman/wav2vec2-large-xlsr-53-turkish" (Farklı ince ayar)
```

### "Yeni bir arayüz teması eklemek istiyorum"
```python
# styles.py, THEMES sözlüğü
THEMES = {
    "dark": { ... },
    "light": { ... },
    "midnight": {  # Yeni temanız
        "bg": "#0a0a2e",
        "fg": "#1a1a4e",
        "accent": "#00d4ff",
        # ... diğer tüm renk anahtarlarını doldurun
    }
}
```

---

## Kaynak Koddan Çalıştırma

```bash
# 1. Sanal ortam oluşturun
python -m venv venv
venv\Scripts\activate

# 2. PyTorch kurun (CUDA 11.8)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 3. WhisperX kurun
pip install git+https://github.com/m-bain/whisperx.git

# 4. Diğer bağımlılıkları kurun
pip install -r requirements.txt

# 5. Çalıştırın
python main.py
```

Whisper Large-v3 modeli (~3.1 GB) ilk çalıştırmada otomatik olarak indirilir.

---

## Mimari Diyagram

```
Kullanıcı BAŞLAT'a basar
       │
       ▼
 ┌─────────────┐    log_q (Kuyruk)     ┌──────────────┐
 │  Arayüz      │◄────────────────────│  İşçi         │
 │  İş Parçacığı │    result_q (Kuyruk) │  Süreç        │
 │  (main_      │◄────────────────────│  (worker.py)  │
 │   window.py) │                      └──────┬───────┘
 └─────────────┘                              │
       │                                      │ çağırır
       │ sonuçları gösterir                   ▼
       ▼                              ┌──────────────┐
 ┌─────────────┐                      │  logic.py    │
 │  Dosya Çıktı │                      │  (Miller +   │
 │  (SRT/JSON/  │                      │   Chronos)   │
 │   TXT)       │                      └──────────────┘
 └─────────────┘
```

Arayüz ve yapay zeka motoru **ayrı süreçlerde** çalışır ve iki kuyrukla bağlanır:
- `log_q`: İşçi süreç log mesajları gönderir → Arayüz log kutusunda gösterir.
- `result_q`: İşçi süreç sonuçları gönderir → Arayüz çıktı dosyalarını yazar.

Bu sayede ağır GPU işlemleri sırasında bile arayüz asla donmaz.

---

*İyi kodlamalar!*
