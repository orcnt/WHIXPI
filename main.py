"""
WHIXPI Pro V1.0 - Entry Point
==============================
Uygulama giriş noktası.

Çalıştırma:
    python main.py
    veya
    Baslat.bat

Geliştirici: @antigravity.studio
"""

import os
import sys
import warnings
import logging
import multiprocessing

# --- FIX: PyInstaller GUI Console NoneType Error ---
class NullWriter:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass

if sys.stdout is None: sys.stdout = NullWriter()
if sys.stderr is None: sys.stderr = NullWriter()

# --- HER ŞEYDEN ÖNCE: DPI AWARENESS ---
try:
    import ctypes
    # Per-monitor DPI awareness (Level 2) - Windows 8.1+
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except AttributeError:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# --- APP USER MODEL ID (Taskbar) ---
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("antigravity.whixpi.pro.v1.0")
except:
    pass

# --- MULTIPROCESSING SETUP ---
try:
    import torch.multiprocessing as mp
    if multiprocessing.get_start_method(allow_none=True) is None:
        mp.set_start_method('spawn', force=True)
except:
    pass

# --- WARNING SUPPRESSION ---
warnings.filterwarnings("ignore")
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("speechbrain").setLevel(logging.ERROR)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# --- CACHE DIRS ---
from pathlib import Path
user_home = Path.home()
os.environ["HF_HOME"] = str(user_home / ".cache" / "huggingface")
os.environ["TORCH_HOME"] = str(user_home / ".cache" / "torch")


def main():
    """Ana uygulama fonksiyonu."""
    from src.ui.main_window import WhisperXApp
    
    app = WhisperXApp()
    app.mainloop()


if __name__ == "__main__":
    # Multiprocessing için freeze desteği (PyInstaller)
    multiprocessing.freeze_support()
    main()
