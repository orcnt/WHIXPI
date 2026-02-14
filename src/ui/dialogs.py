"""
WHIXPI Pro V1.0 - Custom Dialogs
=================================
Özel diyalog pencereleri.
"""

import customtkinter as ctk


class CustomNamingDialog(ctk.CTkToplevel):
    """
    Dosya isimlendirme için özel diyalog penceresi.
    Kullanıcının çıktı dosyalarını manuel olarak adlandırmasını sağlar.
    """
    
    def __init__(self, parent, base_name, formats, callback, locale_dict, theme):
        """
        Args:
            parent: Ana pencere referansı
            base_name: Varsayılan dosya adı
            formats: Aktif formatlar dict'i {"sentence": bool, "word": bool, ...}
            callback: Kaydet butonuna basıldığında çağrılacak fonksiyon
            locale_dict: Çeviri sözlüğü
            theme: Tema renk paleti
        """
        super().__init__(parent)
        
        self.callback = callback
        self.L = locale_dict
        self.theme = theme
        self.result = {}
        
        # Pencere ayarları
        self.title(self.L.get("save_titles", "Dosya İsimleri"))
        self.geometry("500x400")
        self.resizable(False, False)
        self.configure(fg_color=theme.get("bg", "#000000"))
        
        # Modalite
        self.transient(parent)
        self.grab_set()
        
        # Ana container
        container = ctk.CTkFrame(self, fg_color=theme.get("fg", "#1a1a1a"), corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        ctk.CTkLabel(
            container, 
            text=self.L.get("save_titles", "Dosya İsimleri"),
            font=("Arial", 18, "bold"),
            text_color=theme.get("accent", "#E67E22")
        ).pack(pady=(20, 15))
        
        # Entry'leri oluştur
        self.entries = {}
        
        format_labels = {
            "sentence": self.L.get("fmt_srt_sent", "SRT (Cümle)"),
            "word": self.L.get("fmt_srt_word", "SRT (Kelime)"),
            "json": self.L.get("fmt_json", "JSON"),
            "txt_flat": self.L.get("fmt_txt_flat", "TXT (Düz)"),
            "txt_time": self.L.get("fmt_txt_time", "TXT (Zamanlı)")
        }
        
        for key, is_active in formats.items():
            if is_active:
                row = ctk.CTkFrame(container, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=5)
                
                ctk.CTkLabel(
                    row, 
                    text=format_labels.get(key, key) + ":",
                    text_color=theme.get("text", "#cccccc"),
                    width=150,
                    anchor="w"
                ).pack(side="left")
                
                entry = ctk.CTkEntry(
                    row,
                    width=280,
                    fg_color=theme.get("input_bg", "#1a1a1a"),
                    text_color=theme.get("text", "#cccccc"),
                    border_color=theme.get("border", "#333333")
                )
                
                # Yerelleştirilmiş sonek (Varsayılan isim)
                suffix = self.L.get(f"suffix_{key}", f"_{key}")
                entry.insert(0, f"{base_name}{suffix}")
                entry.pack(side="right")
                
                self.entries[key] = entry
        
        # Butonlar
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text=self.L.get("save_btn", "KAYDET"),
            fg_color=theme.get("accent", "#E67E22"),
            hover_color=theme.get("accent_hover", "#D35400"),
            font=("Arial", 14, "bold"),
            width=150,
            height=40,
            command=self.on_save
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="İptal",
            fg_color=theme.get("del_btn", "#c0392b"),
            hover_color=theme.get("del_hover", "#e74c3c"),
            font=("Arial", 14, "bold"),
            width=100,
            height=40,
            command=self.destroy
        ).pack(side="left", padx=10)
        
        # Pencereyi ortala
        self.center_window()
    
    def center_window(self):
        """Pencereyi ekranın ortasına konumlandırır."""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")
    
    def on_save(self):
        """Kaydet butonuna basıldığında."""
        for key, entry in self.entries.items():
            self.result[key] = entry.get().strip()
        
        self.destroy()
        
        if self.callback:
            self.callback(self.result)


class ProgressDialog(ctk.CTkToplevel):
    """
    İlerleme göstergesi diyaloğu.
    Uzun işlemler sırasında kullanıcıya feedback verir.
    """
    
    def __init__(self, parent, title, message, theme):
        """
        Args:
            parent: Ana pencere
            title: Diyalog başlığı
            message: Gösterilecek mesaj
            theme: Tema renk paleti
        """
        super().__init__(parent)
        
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        self.configure(fg_color=theme.get("bg", "#000000"))
        
        self.transient(parent)
        self.grab_set()
        
        # Container
        container = ctk.CTkFrame(self, fg_color=theme.get("fg", "#1a1a1a"), corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Mesaj
        self.message_label = ctk.CTkLabel(
            container,
            text=message,
            font=("Arial", 14),
            text_color=theme.get("text", "#cccccc")
        )
        self.message_label.pack(pady=(20, 15))
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(
            container,
            width=300,
            progress_color=theme.get("accent", "#E67E22")
        )
        self.progress.pack(pady=10)
        self.progress.set(0)
        
        self.center_window()
    
    def center_window(self):
        """Pencereyi ortalar."""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    
    def update_progress(self, value, message=None):
        """
        İlerlemeyi günceller.
        
        Args:
            value: 0.0 - 1.0 arası ilerleme değeri
            message: Opsiyonel yeni mesaj
        """
        self.progress.set(value)
        if message:
            self.message_label.configure(text=message)
        self.update()


class ConfirmDialog(ctk.CTkToplevel):
    """
    Onay diyaloğu.
    Kullanıcıdan evet/hayır onayı alır.
    """
    
    def __init__(self, parent, title, message, theme, on_confirm=None, on_cancel=None):
        """
        Args:
            parent: Ana pencere
            title: Başlık
            message: Mesaj
            theme: Tema
            on_confirm: Onay callback'i
            on_cancel: İptal callback'i
        """
        super().__init__(parent)
        
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.result = False
        
        self.title(title)
        self.geometry("400x180")
        self.resizable(False, False)
        self.configure(fg_color=theme.get("bg", "#000000"))
        
        self.transient(parent)
        self.grab_set()
        
        container = ctk.CTkFrame(self, fg_color=theme.get("fg", "#1a1a1a"), corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            container,
            text=message,
            font=("Arial", 14),
            text_color=theme.get("text", "#cccccc"),
            wraplength=350
        ).pack(pady=(25, 20))
        
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Evet",
            fg_color=theme.get("success_btn", "#27ae60"),
            hover_color="#2ecc71",
            width=100,
            command=self._on_yes
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Hayır",
            fg_color=theme.get("del_btn", "#c0392b"),
            hover_color=theme.get("del_hover", "#e74c3c"),
            width=100,
            command=self._on_no
        ).pack(side="left", padx=10)
        
        self.center_window()
    
    def center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    
    def _on_yes(self):
        self.result = True
        self.destroy()
        if self.on_confirm:
            self.on_confirm()
    
    def _on_no(self):
        self.result = False
        self.destroy()
        if self.on_cancel:
            self.on_cancel()
