"""
WHIXPI Pro V1.0 - UI Styles
============================
Renk paletleri ve tema tanımları.
"""

# =============================================================================
# TEMA PALETLERI
# =============================================================================

THEMES = {
    "dark": {
        # Ana Renkler
        "bg": "#000000",              # Ana arka plan (siyah)
        "fg": "#1a1a1a",              # Kart/Panel arka planı
        "input_bg": "#1a1a1a",        # Input alanları arka planı
        
        # Vurgu Renkleri
        "accent": "#E67E22",          # Ana vurgu (turuncu)
        "accent_hover": "#D35400",    # Vurgu hover
        
        # Metin Renkleri
        "text": "#cccccc",            # Ana metin
        "text_sec": "gray",           # İkincil metin
        
        # Buton Renkleri
        "del_btn": "#c0392b",         # Silme butonu (kırmızı)
        "del_hover": "#e74c3c",       # Silme hover
        "folder_btn": "#6C3483",      # Klasör seçim butonu (mor)
        "success_btn": "#27ae60",     # Başarı butonu (yeşil)
        
        # Özel Alanlar
        "tab_selected": "#E67E22",    # Seçili tab
        "progress_bar": "#E67E22",    # İlerleme çubuğu
        "border": "#333333",          # Kenarlık rengi
    },
    
    "light": {
        # Ana Renkler
        "bg": "#ecf0f1",              # Ana arka plan (açık gri)
        "fg": "#ffffff",              # Kart/Panel arka planı
        "input_bg": "#ffffff",        # Input alanları arka planı
        
        # Vurgu Renkleri
        "accent": "#2980b9",          # Ana vurgu (mavi)
        "accent_hover": "#3498db",    # Vurgu hover
        
        # Metin Renkleri
        "text": "#2c3e50",            # Ana metin
        "text_sec": "#7f8c8d",        # İkincil metin
        
        # Buton Renkleri
        "del_btn": "#e74c3c",         # Silme butonu
        "del_hover": "#c0392b",       # Silme hover
        "folder_btn": "#8e44ad",      # Klasör seçim butonu
        "success_btn": "#27ae60",     # Başarı butonu
        
        # Özel Alanlar
        "tab_selected": "#2980b9",    # Seçili tab
        "progress_bar": "#2980b9",    # İlerleme çubuğu
        "border": "#bdc3c7",          # Kenarlık rengi
    }
}


# =============================================================================
# FONT TANIMLARI
# =============================================================================

FONTS = {
    "title": ("Arial", 24, "bold"),
    "heading": ("Arial", 18, "bold"),
    "subheading": ("Arial", 14, "bold"),
    "body": ("Arial", 12),
    "small": ("Arial", 10),
    "monospace": ("Consolas", 12),
    "button": ("Arial", 14, "bold"),
    "button_large": ("Arial", 20, "bold"),
}


# =============================================================================
# BOYUT SABİTLERİ
# =============================================================================

SIZES = {
    "window_min_width": 1000,
    "window_min_height": 950,
    "window_default": "1000x950",
    
    "button_height": 40,
    "button_height_large": 60,
    
    "entry_width": 450,
    "entry_height": 35,
    
    "corner_radius": 10,
    "corner_radius_small": 6,
    
    "padding_small": 5,
    "padding_medium": 10,
    "padding_large": 20,
}


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def get_theme(theme_name="dark"):
    """
    Tema paletini döndürür.
    
    Args:
        theme_name: "dark" veya "light"
    
    Returns:
        Tema dict'i
    """
    return THEMES.get(theme_name, THEMES["dark"])


def get_color(theme_name, color_key):
    """
    Belirli bir temadan renk döndürür.
    
    Args:
        theme_name: "dark" veya "light"
        color_key: Renk anahtarı ("bg", "accent", vb.)
    
    Returns:
        Renk kodu (hex string)
    """
    theme = get_theme(theme_name)
    return theme.get(color_key, "#000000")
