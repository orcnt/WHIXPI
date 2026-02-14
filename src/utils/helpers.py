"""
WHIXPI Pro V1.0 - Sistem Yardımcıları
=====================================
Windows API entegrasyonu, yol yönetimi ve yerelleştirme araçları.
"""

import os
import sys
import json
import ctypes
from pathlib import Path

# =============================================================================
# WINDOWS API ENTEGRASYONU
# =============================================================================

def enable_high_dpi_awareness():
    """
    Windows High-DPI farkındalığını etkinleştirir.
    Bu, yüksek çözünürlüklü ekranlarda bulanık UI sorununu çözer.
    
    Çağrı Zamanı: main.py'nin en başında, UI yüklenmeden önce.
    """
    try:
        # Windows 8.1+ için Per-Monitor DPI Aware (en iyi sonuç)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except AttributeError:
        try:
            # Windows Vista/7 için fallback
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass
    except Exception:
        pass


def set_app_user_model_id(app_id="antigravity.whixpi.pro.v1"):
    """
    Windows görev çubuğu için uygulama kimliği ayarlar.
    Bu, uygulamanın 'python.exe' yerine kendi ikonuyla gruplanmasını sağlar.
    
    Args:
        app_id: Benzersiz uygulama tanımlayıcısı (string)
    """
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


# =============================================================================
# DOSYA YOLU YÖNETİMİ
# =============================================================================

def get_resource_path(relative_path):
    """
    PyInstaller ile paketlenmiş veya normal çalışma için kaynak dosya yolunu döndürür.
    
    Args:
        relative_path: resources/ klasörüne göre göreceli yol (örn: "icon.ico")
    
    Returns:
        Tam dosya yolu (string)
    """
    try:
        # 1. ONCELIK: EXE'nin yanindaki klasor (Bizim Portable Yapi)
        if getattr(sys, 'frozen', False):
            # PyInstaller ile derlenmis EXE
            exe_dir = os.path.dirname(sys.executable)
            target_path = os.path.join(exe_dir, "resources", relative_path)
            
            # Eger EXE yaninda dosya varsa onu kullan
            if os.path.exists(target_path):
                return target_path
            
            # 2. ONCELIK: PyInstaller _internal klasoru (Yedek)
            base_path = sys._MEIPASS
        else:
            # Normal Python calismasi
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    except AttributeError:
        # Hata durumunda yine normal yola dus
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    return os.path.join(base_path, "resources", relative_path)


def get_unique_path(path):
    """
    Dosya zaten varsa, benzersiz bir isim oluşturur.
    Örnek: video.srt → video (1).srt → video (2).srt
    
    Args:
        path: Hedef dosya yolu (Path veya string)
    
    Returns:
        Benzersiz dosya yolu (string)
    """
    path = Path(path)
    if not path.exists():
        return str(path)
    
    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    counter = 1
    
    while True:
        new_path = parent / f"{stem} ({counter}){suffix}"
        if not new_path.exists():
            return str(new_path)
        counter += 1


# =============================================================================
# WINDOWS DRAG-AND-DROP (SÜRÜKLE-BIRAK) DESTEĞİ
# =============================================================================

import queue
from ctypes import wintypes

# Global DND kuyruğu - bırakılan dosyalar buraya eklenir
_dnd_queue = queue.Queue()

# Windows API tanımlamaları
try:
    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32
    
    # DragQueryFileW fonksiyon imzası
    shell32.DragQueryFileW.argtypes = [ctypes.c_void_p, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
    shell32.DragQueryFileW.restype = wintypes.UINT
    shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
    
    # 64-bit veya 32-bit Windows uyumu
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        # 64-bit Windows
        WNDPROC_TYPE = ctypes.WINFUNCTYPE(ctypes.c_longlong, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
        SET_WND = user32.SetWindowLongPtrW
        CALL_WND = user32.CallWindowProcW
        SET_WND.restype = ctypes.c_void_p
        SET_WND.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
        CALL_WND.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        CALL_WND.restype = ctypes.c_longlong
    else:
        # 32-bit Windows
        WNDPROC_TYPE = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
        SET_WND = user32.SetWindowLongW
        CALL_WND = user32.CallWindowProcW
        SET_WND.restype = ctypes.c_long
        SET_WND.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
        CALL_WND.argtypes = [ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        CALL_WND.restype = ctypes.c_long

except Exception:
    # Windows dışı sistemlerde hata vermemesi için
    user32 = None
    shell32 = None
    WNDPROC_TYPE = None
    SET_WND = None
    CALL_WND = None

# Eski pencere prosedürü referansı (hook için gerekli)
_old_wndproc = None
_new_wndproc = None  # Garbage collection'dan korumak için


def global_wnd_proc(hwnd, msg, wparam, lparam):
    """
    Windows mesaj kancası - WM_DROPFILES mesajını yakalar.
    Sürüklenen dosyaları _dnd_queue kuyruğuna ekler.
    """
    global _old_wndproc
    
    try:
        WM_DROPFILES = 0x0233
        
        if msg == WM_DROPFILES:
            hdrop = ctypes.c_void_p(wparam)
            
            # Dosya sayısını al
            num_files = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
            
            # Her dosyayı kuyruğa ekle
            for i in range(num_files):
                length = shell32.DragQueryFileW(hdrop, i, None, 0)
                buffer = ctypes.create_unicode_buffer(length + 1)
                shell32.DragQueryFileW(hdrop, i, buffer, length + 1)
                _dnd_queue.put(buffer.value)
            
            # Handle'ı serbest bırak
            shell32.DragFinish(hdrop)
            return 0
            
    except Exception:
        pass
    
    # Diğer mesajları orijinal prosedüre ilet
    return CALL_WND(_old_wndproc, hwnd, msg, wparam, lparam)


# =============================================================================
# YERELLEŞTİRME YÖNETİMİ (LOCALIZATION)
# =============================================================================

class LocaleManager:
    """
    JSON tabanlı çoklu dil desteği yöneticisi.
    
    Kullanım:
        L = LocaleManager("locales/")
        L.load_locale("tr")
        print(L.get("start_btn"))  # "BAŞLAT"
    """
    
    def __init__(self, locales_dir_unused):
        """
        Args:
            locales_dir_unused: (Artik kullanilmiyor, dinamik buluyoruz)
        """
        # 1. ONCELIK: EXE'nin yanindaki klasor
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            target_path = os.path.join(exe_dir, "locales")
            
            if os.path.exists(target_path):
                self.locales_dir = target_path
            else:
                self.locales_dir = os.path.join(sys._MEIPASS, "locales")
        else:
            # Normal Calisma
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.locales_dir = os.path.join(base_dir, "locales")

        self.current_locale = {}
        self.lang_code = "tr"
    
    def load_locale(self, lang_code):
        """
        Belirtilen dil koduna göre JSON dosyasını yükler.
        
        Args:
            lang_code: Dil kodu ("tr", "en" vb.)
        
        Returns:
            bool: Yükleme başarılı mı
        """
        self.lang_code = lang_code
        json_path = os.path.join(self.locales_dir, f"{lang_code}.json")
        
        try:
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    self.current_locale = json.load(f)
                return True
        except Exception as e:
            print(f"[LocaleManager] Dil dosyası yüklenemedi: {e}")
        
        return False
    
    def get(self, key, default=None):
        """
        Çeviri metnini döndürür.
        
        Args:
            key: Çeviri anahtarı
            default: Bulunamazsa döndürülecek değer (None ise key döner)
        
        Returns:
            Çeviri metni veya varsayılan değer
        """
        return self.current_locale.get(key, default if default is not None else key)
    
    def get_available_languages(self):
        """
        Mevcut dil dosyalarını listeler.
        
        Returns:
            list: Dil kodları ["tr", "en", ...]
        """
        languages = []
        try:
            for file in os.listdir(self.locales_dir):
                if file.endswith(".json"):
                    languages.append(file.replace(".json", ""))
        except Exception:
            pass
        return languages
