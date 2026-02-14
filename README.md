# WHIXPI v1.0

> **[🇹🇷 Türkçe Dokümantasyon için Tıklayın (BENI_OKU.md)](BENI_OKU.md)**



<div align="center">

**Professional Video & Audio Transcription Studio**

[![License: Unlicense](https://img.shields.io/badge/License-Unlicense-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg)](https://python.org)
[![CUDA 11.8+](https://img.shields.io/badge/CUDA-11.8+-76B900.svg)](https://developer.nvidia.com/cuda-toolkit)

*Created by Alparslan Orçun Tarhan*

</div>

---

## About

WHIXPI is a desktop application that converts video and audio files into text with millisecond-level precision, generating professional subtitles in SRT, JSON, and TXT formats.

It leverages state-of-the-art AI models — OpenAI's Whisper for transcription, Meta's Wav2Vec2 for word-level alignment, and Silero VAD for voice activity detection — combined with custom-built algorithms (Miller Hybrid Splitter and Chronos Timing Engine) for subtitle formatting and timing refinement.

**Target users:** Social media content creators, subtitle translators, transcription professionals, and data analysts.

---

## Editions

### Portable Edition (Recommended)
A fully self-contained package. No installation required. Includes the Whisper Large-v3 model and FFmpeg.

- **Files (Split due to GitHub limits):**
  - `WHIXPI_v1.0_Taşınabilir-Portable.7z.001`
  - `WHIXPI_v1.0_Taşınabilir-Portable.7z.002`
  - `WHIXPI_v1.0_Taşınabilir-Portable.7z.003`
- **Usage:** Download all parts into the same folder. Right-click on the **.001** file and select "Extract Here" (using 7-Zip or WinRAR).
- **Size:** ~6 GB total (includes AI model)

### Source Code Edition (For Developers)
Run directly from Python source code.

1. Ensure **Python 3.10+** is installed.
2. Install [PyTorch with CUDA support](https://pytorch.org/get-started/locally/).
3. Install [WhisperX](https://github.com/m-bain/whisperx).
4. Install remaining dependencies: `pip install -r requirements.txt`
5. Run: `python main.py`

See the [Requirements](#requirements) section below for detailed setup instructions.

---

## Features

### AI Engine
- **Whisper Large-v3** — OpenAI's most powerful open-source speech recognition model
- **Wav2Vec2 Alignment** — Millisecond-accurate word-level timestamp alignment
- **Silero VAD** — Intelligent voice activity detection for precise speech boundary detection
- **Diamond Precision** — VAD-powered surgical refinement of start/end timestamps

### Custom Algorithms
- **Miller Hybrid Splitter** — Balanced, aesthetically pleasing subtitle segmentation with line-balancing, conjunction protection, and anti-dangle logic
- **Chronos Timing Engine** — Seamless gap bridging and dynamic timing distribution between words and sentences

### Output Formats

| Format | Use Case |
|:---|:---|
| SRT (Word-level) | YouTube Shorts, Instagram Reels, TikTok |
| SRT (Sentence-level) | Film subtitles, documentaries, long-form video |
| JSON (Raw) | Programmatic processing, data analysis, pipelines |
| TXT (Plain) | Text editors, search indexing, archival |
| TXT (Timestamped) | Detailed log files, manual review |

### Performance Profiles (VRAM Management)

| Profile | VRAM Usage | Batch | Beam | Recommended GPU |
|:---|:---|:---|:---|:---|
| SONIC | 13–14 GB | 32 | 1–5 | RTX 4090 / 3090 |
| ULTRA | ~12 GB | 10 | 20 | RTX 4080 / 3080 |
| HIGH | ~10 GB | 10 | 10 | RTX 4070 / 3070 |
| BALANCED | ~6 GB | 6 | 5 | RTX 4060 / 3060 |
| ECO | 3–4 GB | 1 | 1 | GTX 1650 / 1060 |
| EXPERIMENTAL | Custom | Custom | Custom | Advanced users only |

### Interface
- Dark / Light theme support
- Turkish and English UI languages
- High-DPI awareness (4K display support)
- Native Windows Drag-and-Drop via Win32 API

---

## Project Structure

```
WHIXPI/
├── main.py                 # Application entry point
├── Baslat.bat              # Quick launch script (Windows)
├── requirements.txt        # Python dependencies
├── settings.json           # User settings (auto-generated)
│
├── src/
│   ├── engine/
│   │   ├── logic.py        # Miller Hybrid Splitter & Chronos Timing
│   │   └── worker.py       # AI Transcription Worker (multiprocessing)
│   ├── ui/
│   │   ├── main_window.py  # Main application window
│   │   ├── dialogs.py      # Custom dialog windows
│   │   └── styles.py       # Theme definitions & color palettes
│   └── utils/
│       └── helpers.py      # DPI, DnD, path resolution, localization
│
├── locales/
│   ├── tr.json             # Turkish translations
│   └── en.json             # English translations
│
├── resources/
│   ├── icon.ico            # Application icon
│   └── logo.png            # Application logo
│
├── models/                 # AI models directory (auto-downloaded)
│   └── large-v3/           # Whisper Large-v3 model files
│
└── bin/                    # External tools
    ├── ffmpeg.exe          # Media processing
    └── ffprobe.exe         # Media information
```

---

## Requirements

### System Requirements
- **OS:** Windows 10/11 (64-bit)
- **RAM:** 8 GB minimum (16 GB recommended)
- **GPU:** NVIDIA GPU with 4 GB+ VRAM (CUDA 11.8+)
- **Disk:** ~10 GB free space (for model + application)

### Python Dependencies (Source Code Edition)

**Step 1: Install PyTorch (CUDA 11.8)**
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Step 2: Install WhisperX**
```bash
pip install git+https://github.com/m-bain/whisperx.git
```

**Step 3: Install remaining dependencies**
```bash
pip install -r requirements.txt
```

The `requirements.txt` includes: `customtkinter`, `Pillow`, `numpy`, `scipy`, `transformers`, `ffmpeg-python`.

**Note:** The Whisper Large-v3 model (~3.1 GB) is downloaded automatically on first launch to the `models/` directory.

---

## How to Use

1. **Add Files** — Click the "+ ADD FILE" button or drag-and-drop video/audio files directly onto the window.
2. **Choose Formats** — Select the output formats you need (SRT, JSON, TXT).
3. **Configure** — Adjust VRAM profile, bridging thresholds, and subtitle limits in the Settings and Performance tabs.
4. **Start** — Press the START button. Transcription runs in a background process without freezing the UI.
5. **Results** — Output files are saved to the selected output directory.

---

## Development

### Adding a New Language
1. Create a new JSON file in `locales/` (e.g., `de.json` for German).
2. Copy all keys from `tr.json` and translate the values.
3. The application will detect the new language automatically.

### Customizing Themes
Edit the `THEMES` dictionary in `src/ui/styles.py` to add or modify color palettes.

---

## Third-Party Components & Licenses

WHIXPI is built upon and incorporates the following open-source projects. Each project's copyright belongs to its respective authors and contributors.

**Users who redistribute or modify WHIXPI must comply with the licenses of these third-party components.**

| Component | License | Author / Organization | Link |
|:---|:---|:---|:---|
| OpenAI Whisper | MIT | OpenAI | [github.com/openai/whisper](https://github.com/openai/whisper) |
| WhisperX | BSD-4-Clause | Max Bain | [github.com/m-bain/whisperx](https://github.com/m-bain/whisperx) |
| Faster-Whisper | MIT | SYSTRAN / Guillaume Klein | [github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| CTranslate2 | MIT | OpenNMT | [github.com/OpenNMT/CTranslate2](https://github.com/OpenNMT/CTranslate2) |
| Silero VAD | MIT | snakers4 | [github.com/snakers4/silero-vad](https://github.com/snakers4/silero-vad) |
| PyTorch | BSD-3-Clause | Meta / Facebook AI Research | [pytorch.org](https://pytorch.org/) |
| Transformers | Apache-2.0 | Hugging Face | [github.com/huggingface/transformers](https://github.com/huggingface/transformers) |
| Hugging Face Hub | Apache-2.0 | Hugging Face | [github.com/huggingface/huggingface_hub](https://github.com/huggingface/huggingface_hub) |
| SpeechBrain | Apache-2.0 | SpeechBrain Team | [github.com/speechbrain/speechbrain](https://github.com/speechbrain/speechbrain) |
| Wav2Vec2 XLS-R Turkish | CC BY-NC 4.0* | Özcan Gündeş | [huggingface.co/ozcangundes](https://huggingface.co/ozcangundes/wav2vec2-large-xlsr-53-turkish) |
| FFmpeg | LGPL-2.1+ / GPL | FFmpeg Team | [ffmpeg.org](https://ffmpeg.org/) |
| CustomTkinter | MIT | Tom Schimansky | [github.com/TomSchimansky/CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Pillow (PIL) | HPND | Jeffrey A. Clark (Alex) | [github.com/python-pillow/Pillow](https://github.com/python-pillow/Pillow) |
| NumPy | BSD-3-Clause | NumPy Developers | [numpy.org](https://numpy.org/) |
| SciPy | BSD-3-Clause | SciPy Developers | [scipy.org](https://scipy.org/) |
| ffmpeg-python | Apache-2.0 | Karl Kroening | [github.com/kkroening/ffmpeg-python](https://github.com/kkroening/ffmpeg-python) |

### Special Notes on FFmpeg

FFmpeg is distributed as a pre-compiled binary (`bin/ffmpeg.exe` and `bin/ffprobe.exe`) under the terms of the **LGPL-2.1+** (or GPL, depending on build configuration). WHIXPI does not modify FFmpeg source code; it uses FFmpeg as a separate, external tool for media processing.

FFmpeg source code is available at: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### Special Notes on Wav2Vec2 Turkish Model

The Turkish alignment model (`ozcangundes/wav2vec2-large-xlsr-53-turkish`) may be subject to a **CC BY-NC 4.0** license depending on the model card. This means it may be restricted to non-commercial use. If you plan to use WHIXPI for commercial purposes, please verify the license terms of this specific model or use an alternative alignment model.

---

## License

This project's own code is released into the public domain under **[The Unlicense](LICENSE)**.

You are free to copy, modify, publish, use, compile, sell, or distribute this software for any purpose, commercial or non-commercial.

A credit to the original creator (**Alparslan Orçun Tarhan**) is appreciated but not required.

**However**, please note that third-party components bundled with or used by WHIXPI are subject to their own licenses (see table above). You must comply with those licenses when redistributing.

---

<div align="center">

*Every voice has a text. Every text has a timestamp.*

</div>
