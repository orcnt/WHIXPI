# WHIXPI v1.0 — Developer Guide / Geliştirici Rehberi

> This guide is for developers who want to understand, modify, or build upon WHIXPI.
> Bu rehber, WHIXPI'yi anlamak, değiştirmek veya üzerine inşa etmek isteyen geliştiriciler içindir.

---

## How the AI Pipeline Works / Yapay Zeka Boru Hattı Nasıl Çalışır

When the user presses "START", the following 4-step pipeline runs in a **separate process** (so the UI never freezes):

Kullanıcı "BAŞLAT" butonuna bastığında, aşağıdaki 4 adımlı süreç **ayrı bir işlemde** çalışır (böylece arayüz asla donmaz):

```
┌─────────────────────────────────────────────────────────┐
│  Step 1: TRANSCRIPTION (worker.py)                      │
│  Whisper Large-v3 sesi metne çevirir.                   │
│  Input:  audio file (.mp4, .wav, etc.)                  │
│  Output: raw segments with approximate timestamps       │
├─────────────────────────────────────────────────────────┤
│  Step 2: ALIGNMENT (worker.py)                          │
│  Wav2Vec2 her kelimeyi ses dalgasıyla eşleştirir.       │
│  Input:  raw segments from Step 1                       │
│  Output: word-level timestamps (millisecond precision)  │
├─────────────────────────────────────────────────────────┤
│  Step 3: DIAMOND REFINERY + CHRONOS (worker.py)         │
│  Silero VAD ile başlangıç/bitiş zamanları rafine edilir │
│  Chronos ile kelime/cümle arası boşluklar köprülenir    │
│  Input:  aligned segments from Step 2                   │
│  Output: refined timestamps                             │
├─────────────────────────────────────────────────────────┤
│  Step 4: MILLER HYBRID SPLIT (logic.py)                 │
│  Metin, dengeli altyazı bloklarına bölünür              │
│  Input:  refined segments from Step 3                   │
│  Output: final SRT/JSON/TXT files                       │
└─────────────────────────────────────────────────────────┘
```

---

## File Map / Dosya Haritası

### `main.py` — Entry Point / Giriş Noktası
- Sets up DPI awareness, multiprocessing, and logging suppression.
- Calls `WhisperXApp().mainloop()` to start the UI.
- DPI farkındalığı, çoklu işlem ve log bastırmayı ayarlar.
- Arayüzü başlatır.

### `src/engine/worker.py` — The Brain / Beyin
- **The most important file.** Contains the entire AI pipeline.
- Runs as a `multiprocessing.Process` so the UI stays responsive.
- Handles: model loading, transcription, alignment, VAD refinement.
- Communicates with the UI via `log_q` (log messages) and `result_q` (results).
- **En önemli dosya.** Tüm AI boru hattını içerir.
- Arayüzün donmaması için ayrı bir işlem olarak çalışır.

**Key functions / Önemli fonksiyonlar:**
- `run()` — Main pipeline orchestrator / Ana boru hattı yöneticisi
- `diamond_refinery()` — VAD-based timestamp refinement / VAD tabanlı zaman iyileştirme
- `analyze_vad_params()` — Auto-calibrates VAD sensitivity / VAD hassasiyetini otomatik ayarlar
- `get_vad_model()` — Loads and caches Silero VAD / Silero VAD'ı yükler ve önbelleğe alır

### `src/engine/logic.py` — Custom Algorithms / Özel Algoritmalar
Contains the two signature algorithms that make WHIXPI's output unique:

- **`miller_hybrid_split()`** — Splits text into balanced subtitle blocks.
  Handles: line balancing, conjunction protection ("ve", "ama" satır sonunda kalmaz),
  anti-dangle (tek kelime sarkmaz), character/word/line limits.

- **`chronos_seamless_core()`** — Bridges gaps between segments.
  If two segments are closer than the threshold, it closes the gap.

- **`waveform_finetune_chronos()`** — Distributes micro-gaps between words.

### `src/ui/main_window.py` — The Face / Yüz
- The main application window. Contains all UI logic.
- Tab management (Transcription, Settings, Performance).
- File queue management, settings save/load, theme switching.

### `src/ui/styles.py` — Colors & Fonts / Renkler & Fontlar
- `THEMES` dict: Dark and Light color palettes.
- `FONTS` dict: Font definitions.
- `SIZES` dict: Window and widget dimensions.
- **To add a new theme:** Add a new key to `THEMES` with the same color keys.

### `src/ui/dialogs.py` — Pop-up Windows / Açılır Pencereler
- `CustomNamingDialog`: Manual file naming dialog.
- `ProgressDialog`: Progress indicator.
- `ConfirmDialog`: Yes/No confirmation.

### `src/utils/helpers.py` — Utilities / Araçlar
- `get_resource_path()`: Finds icons/logos (works both in Python and EXE mode).
- `LocaleManager`: JSON-based translation system.
- `enable_high_dpi_awareness()`: Windows DPI fix.
- Windows Drag-and-Drop via Win32 API hooks.

### `locales/tr.json` & `en.json` — Translations / Çeviriler
- Every UI text is a key-value pair.
- To add a new language: copy `tr.json`, rename to `xx.json`, translate values.
- The app detects new languages automatically.

---

## Common Modifications / Sık Yapılan Değişiklikler

### "I want to change the AI model"
```python
# worker.py, line ~235
model = whisperx.load_model(
    "large-v3",  # Change this to "medium", "small", "large-v3-turbo", etc.
    device,
    compute_type=compute_type,
    ...
)
```

### "I want to add a new VRAM profile"
```python
# worker.py, v_map dictionary (~line 121)
v_map = {
    "vram_sonic": (32, 1, "float16"),
    "vram_my_custom": (16, 10, "float16"),  # Add your profile here
    ...
}
# Then add a matching radio button in main_window.py, setup_perf_tab()
```

### "I want to change subtitle splitting rules"
```python
# logic.py, miller_hybrid_split() function
# Key variables:
#   mw = max words per subtitle block
#   ml = max lines per subtitle block
#   base_l = max characters per line
#   conjunctions = words that should not end a line
```

### "I want to add a new output format"
```python
# main_window.py, look for where SRT/JSON/TXT files are written
# (search for "write" or "save" in the file output section)
# Add your format logic there.
```

### "I want to change the Turkish alignment model"
```python
# worker.py, ~line 277
align_model_name = (
    "ozcangundes/wav2vec2-large-xlsr-53-turkish"  # Change this
    if self.lang == "tr" else None
)
```

---

## Running from Source / Kaynak Koddan Çalıştırma

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install PyTorch (CUDA 11.8)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 3. Install WhisperX
pip install git+https://github.com/m-bain/whisperx.git

# 4. Install other dependencies
pip install -r requirements.txt

# 5. Run
python main.py
```

The Whisper Large-v3 model (~3.1 GB) downloads automatically on first run.

---

## Architecture Diagram / Mimari Diyagram

```
User clicks START
       │
       ▼
 ┌─────────────┐    log_q (Queue)     ┌──────────────┐
 │  UI Thread   │◄────────────────────│  Worker       │
 │  (main_      │    result_q (Queue)  │  Process      │
 │   window.py) │◄────────────────────│  (worker.py)  │
 └─────────────┘                      └──────┬───────┘
       │                                      │
       │ displays results                     │ calls
       ▼                                      ▼
 ┌─────────────┐                      ┌──────────────┐
 │  File Output │                      │  logic.py    │
 │  (SRT/JSON/  │                      │  (Miller +   │
 │   TXT)       │                      │   Chronos)   │
 └─────────────┘                      └──────────────┘
```

The UI and the AI engine run in **separate processes** connected by two queues:
- `log_q`: Worker sends log messages → UI displays them in the log box.
- `result_q`: Worker sends results → UI writes output files.

This means the UI never freezes, even during heavy GPU operations.

---

*Happy coding! / İyi kodlamalar!*
