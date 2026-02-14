"""
WHIXPI Pro V1.0 - Main Window
==============================
Ana uygulama penceresi ve tab kontrolü.
"""

import os
import sys
import json
import subprocess
import multiprocessing
from pathlib import Path
from tkinter import filedialog, messagebox
import ctypes # Windows Taskbar Icon Fix için gerekli

import customtkinter as ctk
from PIL import Image, ImageTk

# Modüler importlar
from src.utils.helpers import (
    LocaleManager, 
    get_resource_path, 
    get_unique_path,
    _dnd_queue,
    shell32,
    WNDPROC_TYPE,
    SET_WND,
    _old_wndproc
)
import src.utils.helpers as helpers
from src.ui.styles import THEMES, FONTS, SIZES
from src.ui.dialogs import CustomNamingDialog
from src.engine.worker import TranscriptionWorker


class WhisperXApp(ctk.CTk):
    """
    Ana WHIXPI uygulaması.
    CustomTkinter tabanlı modern arayüz.
    """
    
    def __init__(self):
        super().__init__()
        
        # --- WINDOWS TASKBAR ICON FIX ---
        # Bu sihirli kod olmazsa, Windows görev çubuğunda "Python Resmi" çıkar.
        try:
            myappid = 'antigravity.whixpi.pro.v1' # keyfi bir ID
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
        
        # --- PATHS & MANAGERS ---
        # --- PATHS & MANAGERS ---
        # settings.json dosyasini da EXE yaninda arayalim
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        # LocaleManager artik yolu kendi buluyor, arguman onemsiz
        self.L = LocaleManager(None)
        self.settings_file = os.path.join(self.base_dir, "settings.json")
        
        # --- LOAD SETTINGS ---
        self.saved_settings = self.load_settings()
        self.CURR_LANG = self.saved_settings.get("language", "tr")
        self.CURR_THEME = self.saved_settings.get("theme", "dark")
        self.L.load_locale(self.CURR_LANG)
        
        # --- APP CONFIG ---
        self.title(self.L.get("title", "WHIXPI v1.0 PRO"))
        self.geometry(SIZES["window_default"])
        self.minsize(SIZES["window_min_width"], SIZES["window_min_height"])
        ctk.set_appearance_mode(self.CURR_THEME)
        
        # --- INITIALIZE VARIABLES ---
        self.init_variables()
        
        # --- WORKER & QUEUES ---
        self.is_running = False
        self.current_worker = None
        self.queue_files = []
        self.log_q = multiprocessing.Queue()
        self.result_q = multiprocessing.Queue()
        
        # --- UI SETUP ---
        self.reload_ui()
        
        # --- ICON SETUP (Hız + Sigorta) ---
        self.apply_master_icon()           # Hemen uygula
        self.after(1000, self.apply_master_icon)  # 1sn sonra tekrar (CTk override sigortası)
        
        # --- WINDOWS DND HOOK ---
        self.after(500, self.setup_dnd)
        
        # --- LOOPING TASKS ---
        self.check_logs()
        self.check_results()
        
        # --- CLOSE EVENT ---
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def init_variables(self):
        """Uygulama değişkenlerini başlatır."""
        s = self.saved_settings
        
        # VRAM & Performance
        self.vram_profile = s.get("vram_profile", "vram_eko")
        self.bridge_ms = s.get("bridge_ms", 700)
        self.word_bridge_ms = s.get("word_bridge_ms", 300)
        self.diamond_precision = s.get("diamond_precision", True)
        self.diamond_sens = s.get("diamond_sens", 50)
        self.diamond_auto = s.get("diamond_auto", True)
        self.stitch_active = s.get("stitch_active", True)
        self.man_batch_val = s.get("manual_batch_size", 8)
        
        # Format checkboxes
        f = s.get("formats", {})
        self.chk_js = ctk.BooleanVar(value=f.get("json", True))
        self.chk_tx = ctk.BooleanVar(value=f.get("txt_flat", True))
        self.chk_tt = ctk.BooleanVar(value=f.get("txt_time", False))
        self.chk_ws = ctk.BooleanVar(value=f.get("srt_word", True))
        self.chk_ls = ctk.BooleanVar(value=f.get("srt_sent", True))
        
        # Settings vars
        self.stitch_var = ctk.BooleanVar(value=self.stitch_active)
        self.vram_var = ctk.StringVar(value=self.vram_profile)
        
        # Options
        opt = s.get("options", {})
        self.man_n = ctk.BooleanVar(value=opt.get("manual_name", False))
        self.auto_o = ctk.BooleanVar(value=opt.get("auto_open", True))
        
        # Performance
        perf = s.get("perf_options", {})
        self.perf_beam_var = ctk.IntVar(value=perf.get("beam_size", 5))
        self.mem_flush_var = ctk.BooleanVar(value=perf.get("mem_flush", False))
        self.base_limit_var = ctk.IntVar(value=perf.get("base_limit", 75))
        self.perf_context_var = ctk.StringVar(value=perf.get("context_prompt", ""))
    
    def apply_master_icon(self):
        """Uygulama ikonunu ayarlar."""
        ico_path = get_resource_path("icon.ico")
        png_path = get_resource_path("new_new_logo.png")
        
        try:
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
            
            if os.path.exists(png_path):
                img = Image.open(png_path)
                render_img = img.resize((256, 256), Image.Resampling.LANCZOS)
                self.master_icon_ref = ImageTk.PhotoImage(render_img)
                self.wm_iconphoto(True, self.master_icon_ref)
        except Exception as e:
            print(f"Icon Error: {e}")
    
    def load_settings(self):
        """Ayarları dosyadan yükler."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_settings(self):
        """Ayarları dosyaya kaydeder."""
        try:
            data = {
                "language": self.CURR_LANG,
                "theme": self.CURR_THEME,
                "vram_profile": self.vram_var.get(),
                "bridge_ms": self.bridge_ms,
                "word_bridge_ms": self.word_bridge_ms,
                "stitch_active": self.stitch_var.get(),
                "output_path": self.out_p.get() if hasattr(self, 'out_p') else str(Path.home() / "Videos" / "WHIXPI_Output"),
                "formats": {
                    "json": self.chk_js.get(),
                    "txt_flat": self.chk_tx.get(),
                    "txt_time": self.chk_tt.get(),
                    "srt_word": self.chk_ws.get(),
                    "srt_sent": self.chk_ls.get()
                },
                "options": {
                    "manual_name": self.man_n.get(),
                    "auto_open": self.auto_o.get()
                },
                "perf_options": {
                    "beam_size": self.perf_beam_var.get(),
                    "mem_flush": self.mem_flush_var.get(),
                    "base_limit": self.base_limit_var.get(),
                    "context_prompt": self.perf_context_var.get(),
                    # Custom Ayarları Koru (Başka moda geçince silinmesin)
                    "custom_batch": self.man_batch_val if "custom" in self.vram_var.get() else self.saved_settings.get("perf_options", {}).get("custom_batch", 8),
                    "custom_beam": self.perf_beam_var.get() if "custom" in self.vram_var.get() else self.saved_settings.get("perf_options", {}).get("custom_beam", 5)
                },
                "limits": {
                    "lines": self.mx_l.get() if hasattr(self, 'mx_l') else "2",
                    "words": self.mx_w.get() if hasattr(self, 'mx_w') else "0"
                }
            }
            # Ayarları "Mühürlü" olarak güncelle (Runtime için)
            self.saved_settings = data
            
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            # Log'a geri bildirim (Sadece UI tamamen yüklendiyse)
            if hasattr(self, 'log_q'):
                p_name = self.vram_var.get()
                beam = self.perf_beam_var.get()
                batch = self.man_batch_val
                
                # Profil adını güzelleştir
                p_map = {
                    "vram_sonic": "⚡ SONIC",
                    "vram_ultra": "🛡️ ULTRA",
                    "vram_custom": "🔧 DENEYSEL",
                    "vram_high": "⚡ YÜKSEK",
                    "vram_mid": "⚖️ DENGELİ",
                    "vram_eko": "🌑 EKO"
                }
                nice_name = p_map.get(p_name, p_name)
                
                self.log_q.put(f"💾 AYARLAR GÜNCELLENDİ ve MÜHÜRLENDİ: [{nice_name}] Batch: {batch} | Beam: {int(beam)}")
                
                # Butonu Normale Döndür
                if hasattr(self, 'perf_apply_btn'):
                    is_sonic = "sonic" in p_name
                    is_custom = "custom" in p_name
                    if is_sonic or is_custom:
                        ok_text = self.T("sonic_save") if is_sonic else self.T("experimental_save")
                        self.perf_apply_btn.configure(fg_color=self.C("accent"), text=ok_text)
        except Exception as e:
            print(f"Settings save error: {e}")
    
    def T(self, key):
        """Çeviri metni döndürür."""
        return self.L.get(key, key)
    
    def C(self, key):
        """Tema rengi döndürür."""
        return THEMES[self.CURR_THEME].get(key, "#000000")
    
    def reload_ui(self):
        """UI'ı yeniden yükler."""
        for w in self.winfo_children():
            w.destroy()
        
        self.configure(fg_color=self.C("bg"))
        
        # Büyük Başlık
        ctk.CTkLabel(
            self, 
            text=self.T("title"), 
            font=("Impact", 36), 
            text_color=self.C("accent")
        ).pack(pady=15)
        
        # Tab view
        self.tabs = ctk.CTkTabview(
            self,
            fg_color=self.C("bg"),
            segmented_button_selected_color=self.C("accent"),
            segmented_button_selected_hover_color=self.C("accent_hover"),
            segmented_button_unselected_color=self.C("fg"),
        )
        self.tabs.pack(fill="both", expand=False, padx=20, pady=5)
        
        # Tabları oluştur
        t1 = self.tabs.add(self.T("tab_transcribe"))
        t2 = self.tabs.add(self.T("tab_settings"))
        t3 = self.tabs.add(self.T("tab_perf"))
        
        self.setup_transcribe_tab(t1)
        self.setup_settings_tab(t2)
        self.setup_perf_tab(t3)
        
        # Progress & Log
        self.p_bar = ctk.CTkProgressBar(self, progress_color=self.C("accent"))
        self.p_bar.pack(padx=20, pady=(10, 5), fill="x")
        self.p_bar.set(0)
        
        self.log_box = ctk.CTkTextbox(
            self, 
            height=100, 
            fg_color=self.C("fg"), 
            text_color=self.C("text"),
            font=FONTS["monospace"]
        )
        self.log_box.pack(padx=20, pady=5, fill="both", expand=True)
        
        # Start Button
        self.btn_go = ctk.CTkButton(
            self,
            text=self.T("start_btn"),
            height=SIZES["button_height_large"],
            font=FONTS["button_large"],
            fg_color=self.C("accent"),
            hover_color=self.C("accent_hover"),
            command=self.start_process
        )
        self.btn_go.pack(padx=20, pady=15, fill="x")
    
    def setup_transcribe_tab(self, parent):
        """Transkripsiyon tabını oluşturur."""
        f_a = ctk.CTkFrame(parent, fg_color="transparent")
        f_a.pack(expand=False, fill="both", padx=20, pady=5)
        
        # Dil seçimi + Motor etiketi
        f_top = ctk.CTkFrame(f_a, fg_color="transparent")
        f_top.pack(fill="x", pady=5)
        
        f_lang = ctk.CTkFrame(f_top, fg_color="transparent")
        f_lang.pack(side="left", padx=5)
        
        ctk.CTkLabel(f_lang, text=self.T("lang_label"), text_color=self.C("accent"), 
                     font=("Arial", 14, "bold")).pack(side="left", padx=10)
        
        ctk.CTkButton(f_lang, text="TÜRKÇE", width=120, height=35,
                      font=("Arial", 12, "bold" if self.CURR_LANG=="tr" else "normal"),
                      fg_color=self.C("accent") if self.CURR_LANG=="tr" else "#333",
                      command=lambda: self.switch_lang("tr")).pack(side="left", padx=5)
        
        ctk.CTkButton(f_lang, text="ENGLISH", width=120, height=35,
                      font=("Arial", 12, "bold" if self.CURR_LANG=="en" else "normal"),
                      fg_color=self.C("accent") if self.CURR_LANG=="en" else "#333",
                      command=lambda: self.switch_lang("en")).pack(side="left", padx=5)
        
        ctk.CTkLabel(f_top, text=self.T("engine_active"), text_color="gray",
                     font=("Arial", 11, "italic")).pack(side="right", padx=10)
        
        # Dosya butonları (genişletilmiş)
        f_btns = ctk.CTkFrame(f_a, fg_color="transparent")
        f_btns.pack(fill="x", pady=10)
        
        ctk.CTkButton(f_btns, text=self.T("add_file"), height=40,
                      fg_color=self.C("accent"), hover_color=self.C("accent_hover"),
                      command=self.add_files).pack(side="left", padx=5, fill="x", expand=True)
        
        ctk.CTkButton(f_btns, text=self.T("clear_list"), height=40,
                      fg_color=self.C("del_btn"), hover_color=self.C("del_hover"),
                      font=("Arial", 12, "bold"),
                      command=self.clear_queue).pack(side="right", padx=5, fill="x", expand=True)
        
        # Dosya listesi
        self.queue_scroll = ctk.CTkScrollableFrame(f_a, height=110, 
                                                   fg_color=self.C("input_bg"),
                                                   border_width=1, border_color="#333")
        self.queue_scroll.pack(fill="both", pady=5)
        self.update_queue_display()
        
        # Çıktı klasörü
        ctk.CTkLabel(f_a, text=self.T("output_folder"), text_color=self.C("accent"),
                     font=("Arial", 12, "bold"), anchor="w").pack(fill="x", pady=(10,0))
        
        f_out = ctk.CTkFrame(f_a, fg_color="transparent")
        f_out.pack(fill="x", pady=5)
        
        self.out_p = ctk.CTkEntry(f_out, height=35, fg_color=self.C("input_bg"), 
                                  text_color=self.C("text"))
        self.out_p.pack(side="left", fill="x", expand=True)
        
        # Varsayılan: Proje dizinindeki 'output' klasörü
        default_out = str(Path.cwd() / "output")
        if not os.path.exists(default_out):
            try: os.makedirs(default_out)
            except: pass
            
        self.out_p.insert(0, self.saved_settings.get("output_path", default_out))
        
        ctk.CTkButton(f_out, text=self.T("select_folder"), width=120, height=35,
                      fg_color=self.C("folder_btn"),
                      command=self.select_output_folder).pack(side="right", padx=5)
        
        # Çıktı formatları
        ctk.CTkLabel(f_a, text=self.T("output_formats"), text_color=self.C("accent"),
                     font=("Arial", 12, "bold"), anchor="w").pack(fill="x", pady=(10,5))
        
        f_fmt = ctk.CTkFrame(f_a, fg_color=self.C("fg"), corner_radius=10)
        f_fmt.pack(fill="x", pady=5)
        
        formats = [
            (self.T("fmt_json"), self.chk_js),
            (self.T("fmt_txt_flat"), self.chk_tx),
            (self.T("fmt_txt_time"), self.chk_tt),
            (self.T("fmt_srt_word"), self.chk_ws),
            (self.T("fmt_srt_sent"), self.chk_ls)
        ]
        
        for i, (txt, var) in enumerate(formats[:3]):
            ctk.CTkCheckBox(f_fmt, text=txt, variable=var, fg_color=self.C("accent"),
                           text_color=self.C("text")).grid(row=0, column=i, padx=10, pady=10, sticky="w")
        for i, (txt, var) in enumerate(formats[3:]):
            ctk.CTkCheckBox(f_fmt, text=txt, variable=var, fg_color=self.C("accent"),
                           text_color=self.C("text")).grid(row=1, column=i, padx=10, pady=10, sticky="w")
    
    def setup_settings_tab(self, parent):
        """Ayarlar tabını oluşturur - Eski v9.5 versiyonuna uyumlu."""
        # Tema seçimi
        t_frame = ctk.CTkFrame(parent, fg_color="transparent")
        t_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(t_frame, text=self.T("theme_label"), text_color=self.C("accent"),
                     font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkButton(t_frame, text=self.T("theme_dark"), width=120,
                      fg_color=self.C("accent") if self.CURR_THEME=="dark" else "#333",
                      command=lambda: self.switch_theme("dark")).pack(side="left", padx=5)
        ctk.CTkButton(t_frame, text=self.T("theme_light"), width=120,
                      fg_color=self.C("accent") if self.CURR_THEME=="light" else "#333",
                      command=lambda: self.switch_theme("light")).pack(side="left", padx=5)
        
        # Köprüleme slider'ları (50ms adımlarla)
        self.bridge_slider = self.create_slider_stepped(parent, self.T("bridge_label"), self.T("bridge_hint"),
                                                        0, 2000, 40, self.bridge_ms, self.update_bridge)
        self.word_bridge_slider = self.create_slider_stepped(parent, self.T("word_bridge_label"), self.T("bridge_hint"),
                                                             0, 1000, 20, self.word_bridge_ms, self.update_word_bridge)
        
        # Manuel/Klasör checkbox'ları (ortalanmış)
        opt_f = ctk.CTkFrame(parent, fg_color="transparent")
        opt_f.pack(pady=8)
        ctk.CTkCheckBox(opt_f, text=self.T("manual_name"), variable=self.man_n,
                        fg_color=self.C("accent")).pack(side="left", padx=20)
        ctk.CTkCheckBox(opt_f, text=self.T("auto_open"), variable=self.auto_o,
                        fg_color=self.C("accent")).pack(side="left", padx=20)
        
        # Estetik Dengeleme (yanında açıklama)
        st_f = ctk.CTkFrame(parent, fg_color="transparent")
        st_f.pack(pady=5)
        ctk.CTkCheckBox(st_f, text=self.T("stitch_label"), variable=self.stitch_var,
                        fg_color=self.C("accent")).pack(side="left")
        ctk.CTkLabel(st_f, text=self.T("stitch_hint"), text_color="#888",
                     font=("Arial", 14)).pack(side="left", padx=10)
        
        # Preset butonları
        pr_f = ctk.CTkFrame(parent, fg_color="transparent")
        pr_f.pack(pady=8)
        presets = [("preset_reels", 42, 1, 0), ("preset_yt", 85, 2, 0), 
                   ("preset_film", 75, 2, 0), ("preset_raw", 90, 0, 0)]
        for key, chars, lines, words in presets:
            ctk.CTkButton(pr_f, text=self.T(key), width=100, fg_color=self.C("accent"),
                          command=lambda c=chars, l=lines, w=words: self.set_preset(c,l,w)).pack(side="left", padx=5)
        
        # Kısıtlama Ayarları
        lf = ctk.CTkFrame(parent, fg_color=self.C("fg"), corner_radius=10)
        lf.pack(fill="x", padx=20, pady=8)
        
        limits = self.saved_settings.get("limits", {})
        l_row = ctk.CTkFrame(lf, fg_color="transparent")
        l_row.pack(fill="x", padx=15, pady=8)
        self.mx_l = self.create_entry(l_row, self.T("max_lines") + " (0=Sınırsız):", limits.get("lines", "2"))
        self.mx_w = self.create_entry(l_row, self.T("max_words") + " (0=Sınırsız):", limits.get("words", "0"))
        
        bl_row = ctk.CTkFrame(lf, fg_color="transparent")
        bl_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(bl_row, text=self.T("perf_base_limit")).pack(side="left")
        self.bl_lbl = ctk.CTkLabel(bl_row, text=str(self.base_limit_var.get()), 
                                   text_color=self.C("accent"), font=("Arial", 12, "bold"))
        self.bl_lbl.pack(side="right", padx=5)
        ctk.CTkSlider(bl_row, from_=10, to=120, variable=self.base_limit_var, progress_color=self.C("accent"),
                      command=lambda v: self.bl_lbl.configure(text=str(int(float(v))))).pack(side="right", fill="x", expand=True)
        
        # Fabrika Ayarları - geniş buton
        ctk.CTkButton(parent, text=self.T("reset_btn"), fg_color="#1a1a1a", border_width=2,
                      border_color=self.C("accent"), text_color=self.C("accent"), height=40,
                      hover_color="#333", command=self.reset_to_defaults).pack(fill="x", padx=20, pady=10)
    
    def create_slider_stepped(self, parent, label, hint, from_, to, steps, init, command):
        """50ms adımlı slider oluşturur."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row, text=label, text_color=self.C("text")).pack(side="left")
        ctk.CTkLabel(row, text=hint, text_color="#888", font=("Arial", 13)).pack(side="left", padx=5)
        v_lbl = ctk.CTkLabel(row, text=f"{init} ms", text_color=self.C("accent"), font=("Arial", 12, "bold"))
        v_lbl.pack(side="right", padx=5)
        slider = ctk.CTkSlider(row, from_=from_, to=to, number_of_steps=steps, progress_color=self.C("accent"),
                               command=lambda v: [v_lbl.configure(text=f"{int(float(v))} ms"), command(v)])
        slider.set(init)
        slider.pack(side="right", fill="x", expand=True, padx=10)
        return slider
    
    def update_sens_label(self, v):
        """Hassasiyet etiketini günceller."""
        val = int(float(v))
        labels = {0: "Ham/Gürültülü", 25: "Amatör", 50: "Standart", 75: "Temiz", 100: "Stüdyo"}
        lbl = labels.get(val, f"{val}")
        self.sens_lbl.configure(text=f"{val}: {lbl}" if val in labels else str(val))
    
    
    def set_preset(self, chars, lines, words):
        self.base_limit_var.set(chars); self.bl_lbl.configure(text=str(chars))
        self.mx_l.delete(0, "end"); self.mx_l.insert(0, str(lines))
        self.mx_w.delete(0, "end"); self.mx_w.insert(0, str(words))
    
    def reset_to_defaults(self):
        self.base_limit_var.set(75); self.bl_lbl.configure(text="75")
        self.bridge_slider.set(700); self.word_bridge_slider.set(300)
        self.stitch_var.set(True)
        self.mx_l.delete(0, "end"); self.mx_l.insert(0, "2")
        self.mx_w.delete(0, "end"); self.mx_w.insert(0, "0")
    
    def setup_perf_tab(self, parent):
        """Performans tabını oluşturur - v1.0 Final Mantığı."""
        # Başlık ve İkon
        ctk.CTkLabel(parent, text=self.T("perf_title"), font=("Impact", 24), text_color=self.C("accent")).pack(pady=10)
        
        # VRAM Profilleri Konteyner
        of = ctk.CTkFrame(parent, fg_color=self.C("input_bg"), corner_radius=10, border_width=1, border_color="#333")
        of.pack(fill="x", padx=20, pady=5)
        
        # (value, title_key, desc_key)
        profiles = [
            ("vram_sonic", "vram_sonic", "vram_sonic_desc"),
            ("vram_ultra", "vram_ultra", "vram_ultra_desc"), # Eski 16GB Safe
            ("vram_high", "vram_12", "vram_12_desc"),        # Eski 12GB
            ("vram_mid", "vram_8", "vram_8_desc"),           # Eski 8GB
            ("vram_eko", "vram_4", "vram_4_desc"),           # Eski 4GB
            ("vram_custom", "vram_custom", "vram_custom_desc") # Deneysel
        ]

        for val, title_key, desc_key in profiles:
            pf = ctk.CTkFrame(of, fg_color="transparent")
            pf.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkRadioButton(pf, text=self.T(title_key), variable=self.vram_var, value=val,
                               fg_color=self.C("accent"), command=self.on_vram_change).pack(anchor="w")
            
            ctk.CTkLabel(pf, text=self.T(desc_key), text_color="#888", font=("Arial", 13)).pack(anchor="w", padx=25)

        # --- Gelişmiş Kontroller ---
        f_adv = ctk.CTkFrame(parent, fg_color="transparent"); f_adv.pack(fill="x", padx=20, pady=5)
        
        # 1. Zeka Seviyesi (Beam Search)
        f_beam_head = ctk.CTkFrame(f_adv, fg_color="transparent"); f_beam_head.pack(fill="x", pady=(5,0))
        ctk.CTkLabel(f_beam_head, text=self.T("perf_iq_label"), font=("Arial", 14, "bold"), text_color=self.C("accent")).pack(side="left")
        ctk.CTkLabel(f_beam_head, text=f" {self.T('perf_iq_hint')}", font=("Arial", 13, "italic"), text_color="#888").pack(side="left", padx=5)
        
        f_beam = ctk.CTkFrame(f_adv, fg_color="transparent"); f_beam.pack(fill="x", pady=5)
        self.beam_val_label = ctk.CTkLabel(f_beam, text="5 Beam", width=80, font=("Arial", 12, "bold"), text_color=self.C("text"))
        self.beam_val_label.pack(side="left")
        
        self.beam_slider = ctk.CTkSlider(f_beam, from_=1, to=20, number_of_steps=19, variable=self.perf_beam_var,
                                         button_color=self.C("accent"), command=self.update_beam_label)
        self.beam_slider.pack(side="left", fill="x", expand=True, padx=10)
        
        # 2. SONIC Ayarlarını Mühürle Butonu
        self.perf_apply_btn = ctk.CTkButton(f_adv, text=self.T("sonic_save"), height=40, font=("Arial", 12, "bold"),
                                           fg_color="gray", state="disabled", command=self.save_settings)
        self.perf_apply_btn.pack(pady=15, padx=20, fill="x")
        
        # 3. Agresif Bellek Temizliği (Sadece EKO Modda Görünür/Aktif)
        self.perf_mem_flush_var_chk = ctk.CTkCheckBox(f_adv, text=self.T("mem_flush"), variable=self.mem_flush_var, 
                                                     fg_color=self.C("accent"), text_color=self.C("accent"), font=("Arial", 12, "bold"),
                                                     state="disabled") # Varsayılan kapalı/kilitli
        self.perf_mem_flush_var_chk.pack(anchor="w", pady=5)
        
        # 4. Batch Seviyesi (Sadece Gösterge)
        f_batch_head = ctk.CTkFrame(f_adv, fg_color="transparent"); f_batch_head.pack(fill="x", pady=(10,0))
        ctk.CTkLabel(f_batch_head, text=self.T("batch_label"), font=("Arial", 14, "bold"), text_color=self.C("accent")).pack(side="left")
        ctk.CTkLabel(f_batch_head, text=f" {self.T('batch_hint')}", font=("Arial", 13, "italic"), text_color="#888").pack(side="left", padx=5)
        
        f_batch = ctk.CTkFrame(f_adv, fg_color="transparent"); f_batch.pack(fill="x", pady=5)
        self.batch_val_label = ctk.CTkLabel(f_batch, text="8", width=80, font=("Arial", 13, "bold"), text_color=self.C("text"))
        self.batch_val_label.pack(side="left")
        
        if not hasattr(self, 'man_batch_val'): 
            # Kayıtlı özel batch varsa yükle, yoksa 8
            self.man_batch_val = self.saved_settings.get("perf_options", {}).get("custom_batch", 8)

        self.batch_slider = ctk.CTkSlider(f_batch, from_=1, to=32, number_of_steps=31, 
                                         button_color=self.C("accent"), state="disabled",
                                         command=self.update_batch_label) # Start locked
        self.batch_slider.set(self.man_batch_val)
        self.batch_slider.pack(side="left", fill="x", expand=True, padx=10)
        self.update_batch_label(self.man_batch_val) # Label'ı güncelle
        
        # İlk Yükleme Tetiklemesi (SESSİZ - Uyarı YOK)
        self.after(300, lambda: self.on_vram_change(silent=True))

    def on_vram_change(self, silent=False):
        """VRAM profili değiştiğinde."""
        if not hasattr(self, 'beam_slider'): return
        
        v = self.vram_var.get()
        
        # DENEYSEL MOD KONTROLÜ
        if v == "vram_custom":
            # Eğer sessiz moddaysa (açılışta) uyarı verme!
            if not silent:
                msg = (
                    "Deneysel ayarlanabilir mod adı üstünde deneysel bir moddur, "
                    "yapacağınız ayarların ne kadar sistem kaynağı kullanacağını bilmiyorsanız kullanmayın, "
                    "donanımınıza zarar bile verebilirsiniz!"
                )
                resp = messagebox.askyesno("⚠️ DİKKAT: YÜKSEK RİSK", msg, icon="warning")
                if not resp:
                    # İptal edilirse varsayılan ULTRA moda dön
                    self.vram_var.set("vram_ultra")
                    self.on_vram_change()
                    return

        
        # A. TÜM KİLİTLERİ AÇ (Değer atayabilmek için şart)
        self.beam_slider.configure(state="normal")
        self.batch_slider.configure(state="normal")
        self.perf_mem_flush_var_chk.configure(state="normal")
        
        # B. PROFİL DEĞERLERİNİ BELİRLE
        target_beam = 5
        target_batch = 8
        is_sonic = False
        is_eko = False 
        is_custom = False

        if v == "vram_sonic":
            is_sonic = True
            target_batch = 32
            # Sonic slider aralığı 1-5
            self.beam_slider.configure(from_=1, to=5, number_of_steps=4)
            current = self.perf_beam_var.get()
            if current < 1 or current > 5: self.perf_beam_var.set(1)
            
        elif v == "vram_ultra": # Eski 16GB Safe
            target_batch=10; target_beam=20
            self.beam_slider.configure(from_=1, to=20, number_of_steps=19)
            
        elif v == "vram_high": # Eski 12GB
            target_batch=10; target_beam=10
            self.beam_slider.configure(from_=1, to=20, number_of_steps=19)
            
        elif v == "vram_mid": # Eski 8GB
            target_batch=6; target_beam=5
            self.beam_slider.configure(from_=1, to=20, number_of_steps=19)
            
        elif v == "vram_eko": # Eski 4GB
            is_eko = True
            target_batch=1; target_beam=1
            self.beam_slider.configure(from_=1, to=20, number_of_steps=19)
            
        elif v == "vram_custom":
            is_custom = True
            # Değerleri ellememize gerek yok, kullanıcı seçecek.
            # Sadece slider aralıklarını resetle
            self.beam_slider.configure(from_=1, to=20, number_of_steps=19)
            
            # KAYITLI ÖZEL AYARLARI YÜKLE (Hafıza)
            # Eğer kayıtlı bir "custom_batch" varsa, onu kullan. Yoksa o anki değer kalsın.
            saved = self.saved_settings.get("perf_options", {})
            
            # Batch Yükle
            if "custom_batch" in saved:
                target_batch = saved["custom_batch"]
                self.man_batch_val = target_batch # Değeri güncelle
                # UI Update:
                self.batch_slider.set(target_batch)
                self.batch_val_label.configure(text=str(target_batch))
                
            # Beam Yükle
            if "custom_beam" in saved:
                target_beam = saved["custom_beam"]
                self.perf_beam_var.set(target_beam) # UI Variable update
                # UI Zorla Güncelle (Görseli)
                self.beam_slider.set(target_beam)
                self.update_beam_label(target_beam)
            else:
                # Custom seçili ama kayıtlı ayar yoksa, varsayılan 5 beam
                target_beam = 5
                self.perf_beam_var.set(target_beam)
                self.beam_slider.set(target_beam)
                self.update_beam_label(target_beam)

        
        # C. DEĞERLERİ UYGULA (Custom değilse)
        if not is_custom:
            # 1. Batch
            self.man_batch_val = target_batch
            self.batch_slider.set(target_batch)
            self.batch_val_label.configure(text=str(target_batch))
            
            # 2. Beam (Sonic olsa bile default'u set etmiştik, Custom değilse bas geç)
            # Sonic modunda kullanıcı 1-5 arası değiştirebilir, o yüzden sadece Sonic DEĞİLSE ve Custom DEĞİLSE zorla.
            if not is_sonic:
                self.perf_beam_var.set(target_beam)
            
            self.update_beam_label(self.perf_beam_var.get())

        # 3. Agresif Temizlik Yönetimi
        if is_eko:
            # EKO Mod: Zorunlu Açık ve Kilitli (4GB Darboğazı)
            self.mem_flush_var.set(True)
            self.perf_mem_flush_var_chk.configure(state="disabled")
            
        elif is_custom:
            # Custom Mod: Varsayılan Kapalı ama Açılabilir
            self.perf_mem_flush_var_chk.configure(state="normal")
            
            # Eğer açılış değilse (Runtime geçişi) varsayılanı False yap.
            # Açılışsa (silent=True), kayıtlı ayarı (JSON'dan geleni) elleme.
            if not silent:
                 self.mem_flush_var.set(False)
                 
        else:
            # Diğer Modlar: Hız için Zorunlu Kapalı ve Kilitli
            self.mem_flush_var.set(False)
            self.perf_mem_flush_var_chk.configure(state="disabled")

        # Ayarları kaydet
        self.save_settings()

        # D. KİLİTLEME YÖNETİMİ
        
        # 1. Beam Slider & Mühürle Butonu
        # Sonic veya Custom ise AÇIK
        if is_sonic or is_custom:
            self.beam_slider.configure(state="normal", button_color=self.C("accent"))
            self.perf_apply_btn.configure(state="normal", fg_color=self.C("accent"), text_color="white")
            
            # Buton metnini dinamikleştir
            btn_text = self.T("sonic_save") if is_sonic else self.T("experimental_save")
            self.perf_apply_btn.configure(text=btn_text)
            
        else:
            self.beam_slider.configure(state="disabled", button_color="#555")
            self.perf_apply_btn.configure(state="disabled", fg_color="#333", text_color="gray", text=self.T("sonic_save"))
            
        # 2. Batch Slider (Sadece Custom'da açık)
        if is_custom:
             self.batch_slider.configure(state="normal", button_color=self.C("accent"))
        else:
             self.batch_slider.configure(state="disabled", button_color="#555")

    def update_beam_label(self, val):
        if hasattr(self, 'beam_val_label'):
            self.beam_val_label.configure(text=f"{int(float(val))} Beam")
        
        # Değişiklik oldu, butonu uyarı moduna al
        self._notify_change()
            
    def update_batch_label(self, val):
        val_int = int(float(val))
        self.man_batch_val = val_int # Değeri sakla
        if hasattr(self, 'batch_val_label'):
            self.batch_val_label.configure(text=str(val_int))
        
        # Değişiklik oldu, butonu uyarı moduna al
        self._notify_change()
            
    def _notify_change(self):
        """Ayarlar değiştiğinde kullanıcıyı uyarır (Butonu sarı yapar)."""
        if hasattr(self, 'perf_apply_btn') and self.perf_apply_btn._state != "disabled":
            self.perf_apply_btn.configure(fg_color="#F39C12", text="⚠️ DEĞİŞİKLİKLERİ ONAYLA VE MÜHÜRLE")
    
    def create_slider(self, parent, label, from_, to, init, command):
        """Slider oluşturur."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(row, text=label, text_color=self.C("accent"), width=150, anchor="w").pack(side="left")
        
        val_lbl = ctk.CTkLabel(row, text=str(init), width=50, text_color=self.C("text"))
        val_lbl.pack(side="right")
        
        def on_change(v):
            val_lbl.configure(text=str(int(float(v))))
            command(v)
            
        sld = ctk.CTkSlider(row, from_=from_, to=to, number_of_steps=to-from_, command=on_change)
        sld.set(init)
        sld.pack(side="right", fill="x", expand=True, padx=10)
        return sld

    def create_entry(self, parent, label, value):
        """Entry oluşturur."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(row, text=label, text_color=self.C("text"), width=150, anchor="w").pack(side="left")
        
        ent = ctk.CTkEntry(row, width=100)
        ent.insert(0, str(value))
        ent.pack(side="right")
        return ent
    
    # --- ICON MANAGEMENT (WINDOWS API DIRECT) ---
    
    def apply_master_icon(self):
        """
        Windows API ile doğrudan ikon atama.
        Tkinter pipeline'ını tamamen bypass eder.
        ICO dosyasından belirli boyutlardaki katmanları yükler.
        """
        try:
            ico_path = get_resource_path("icon.ico")
            
            if not os.path.exists(ico_path):
                self.log_q.put(f"⚠️ icon.ico bulunamadı: {ico_path}")
                return
            
            import ctypes
            from ctypes import windll
            
            WM_SETICON = 0x80
            ICON_SMALL = 0
            ICON_BIG = 1
            LR_LOADFROMFILE = 0x10
            IMAGE_ICON = 1
            
            # Pencere handle
            hwnd = windll.user32.GetParent(self.winfo_id())
            if hwnd == 0:
                hwnd = self.winfo_id()
            
            # BÜYÜK ikon (Taskbar, Alt+Tab): 48x48
            hicon_big = windll.user32.LoadImageW(
                None, str(ico_path), IMAGE_ICON,
                48, 48,  # Açıkça 48x48 iste
                LR_LOADFROMFILE
            )
            
            # KÜÇÜK ikon (Title bar): 16x16
            hicon_small = windll.user32.LoadImageW(
                None, str(ico_path), IMAGE_ICON,
                16, 16,  # Açıkça 16x16 iste
                LR_LOADFROMFILE
            )
            
            if hicon_big:
                windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
            if hicon_small:
                windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
            
            self.log_q.put(f"🎨 Windows API ikon: big={hicon_big!=0}, small={hicon_small!=0}")
            
        except Exception as e:
            self.log_q.put(f"⚠️ İkon hatası: {e}")

    # --- EVENT HANDLERS ---
    
    def update_bridge(self, v):
        self.bridge_ms = int(float(v))
        self.schedule_save()

    def update_word_bridge(self, v):
        self.word_bridge_ms = int(float(v))
        self.schedule_save()
        
    def schedule_save(self):
        """Ayarları gecikmeli kaydeder (Debounce)."""
        if hasattr(self, "_save_timer") and self._save_timer:
            self.after_cancel(self._save_timer)
        self._save_timer = self.after(1000, self.save_settings)
    
    def switch_lang(self, lang):
        """Dil değiştirir."""
        self.CURR_LANG = lang
        self.L.load_locale(lang)
        self.save_settings()
        self.reload_ui()
    
    def switch_theme(self, theme):
        """Tema değiştirir."""
        self.CURR_THEME = theme
        ctk.set_appearance_mode(theme)
        self.save_settings()
        self.reload_ui()
    
    def select_output_folder(self):
        """Çıktı klasörü seçer."""
        folder = filedialog.askdirectory()
        if folder:
            self.out_p.delete(0, 'end')
            self.out_p.insert(0, folder)
    
    def add_files(self, paths=None):
        """Dosya ekler."""
        if not paths:
            paths = filedialog.askopenfilenames(
                filetypes=[("Media", "*.mp3 *.wav *.m4a *.mp4 *.mkv *.mov *.webm")]
            )
        
        for p in paths:
            if p and p not in self.queue_files:
                self.queue_files.append(p)
                self.log_q.put(f"{self.T('added')} {Path(p).name}")
        
        self.update_queue_display()
    
    def clear_queue(self):
        """Kuyruğu temizler."""
        self.queue_files = []
        self.update_queue_display()
        self.log_q.put(self.T("cleared"))
    
    def update_queue_display(self):
        """Kuyruk görünümünü günceller."""
        for w in self.queue_scroll.winfo_children():
            w.destroy()
        
        for i, p in enumerate(self.queue_files):
            row = ctk.CTkFrame(self.queue_scroll, fg_color=self.C("fg"), height=40)
            row.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkButton(
                row,
                text="X",
                width=30,
                height=30,
                fg_color=self.C("del_btn"),
                hover_color=self.C("del_hover"),
                command=lambda idx=i: self.remove_from_queue(idx)
            ).pack(side="left", padx=10)
            
            ctk.CTkLabel(
                row,
                text=f"{i+1}. {Path(p).name}",
                text_color=self.C("text")
            ).pack(side="left", padx=5)
    
    def remove_from_queue(self, idx):
        """Kuyruktan dosya siler."""
        if 0 <= idx < len(self.queue_files):
            self.queue_files.pop(idx)
            self.update_queue_display()
    
    # --- DND ---
    
    def setup_dnd(self):
        """Drag-and-Drop sistemini kurar."""
        try:
            hwnd = self.winfo_id()
            helpers.shell32.DragAcceptFiles(hwnd, True)
            
            helpers._new_wndproc = helpers.WNDPROC_TYPE(helpers.global_wnd_proc)
            helpers._old_wndproc = helpers.SET_WND(hwnd, -4, helpers._new_wndproc)
            
            self.log_q.put(self.T("dnd_active"))
            self.check_dnd()
        except Exception as e:
            self.log_q.put(self.T("dnd_fail"))
    
    def check_dnd(self):
        """DND kuyruğunu kontrol eder."""
        try:
            while not _dnd_queue.empty():
                file_path = _dnd_queue.get()
                self.add_files([file_path])
        except:
            pass
        self.after(500, self.check_dnd)
    
    # --- PROCESSING ---
    
    def start_process(self):
        """İşlemi başlatır/durdurur."""
        if self.is_running:
            # ZORLA DURDURMA (Terminate)
            if self.current_worker and self.current_worker.is_alive():
                self.log_q.put("🛑 İşlem zorla durduruluyor...")
                self.current_worker.terminate()
                self.current_worker.join(timeout=0.1)
            
            self.is_running = False
            self.current_worker = None
            self.btn_go.configure(text=self.T("start_btn"), state="normal", fg_color=self.C("accent"))
            self.log_q.put("⛔ İşlem iptal edildi.")
            self.p_bar.set(0)
            return
        
        if not self.queue_files:
            messagebox.showwarning("Uyarı", "Lütfen önce dosya ekleyin!")
            return
        
        self.is_running = True
        self.btn_go.configure(text=self.T("stop_btn"), fg_color=self.C("del_btn"))
        
        # Worker Config Hazırlama
        # KRİTİK DÜZELTME: Kullanıcı o an ne görüyorsa o çalışmalı.
        # "Mühürlü ayar" yerine anlık UI değerlerini alıyoruz.
        
        final_beam = self.perf_beam_var.get()
        final_batch = self.man_batch_val
        
        # Sonic veya Custom modda kontrol (Gereksiz karmaşayı önlemek için basitleştirildi)
        curr_vram = self.vram_var.get()
        
        config = {
            "max_lines": self.mx_l.get(),
            "max_words": self.mx_w.get(),
            "base_limit": self.base_limit_var.get(),
            "beam_size": final_beam, 
            "batch_size": final_batch 
        }
        
        self.current_worker = TranscriptionWorker(
            audio_list=self.queue_files.copy(),
            out_dir=self.out_p.get(),
            config=config,
            lang=self.CURR_LANG,
            model_name="large-v3",
            log_q=self.log_q,
            result_q=self.result_q,
            locale_dict=self.L.current_locale,
            vram_profile=self.vram_var.get(),
            align_engine="Wav2Vec2",
            bridge_ms=self.bridge_ms,
            word_bridge_ms=self.word_bridge_ms
        )
        self.current_worker.start()
    
    def done(self, res, is_final):
        """İşlem tamamlandığında."""
        if res:
            if self.man_n.get():
                formats = {
                    "sentence": self.chk_ls.get(),
                    "word": self.chk_ws.get(),
                    "json": self.chk_js.get(),
                    "txt_flat": self.chk_tx.get(),
                    "txt_time": self.chk_tt.get()
                }
                CustomNamingDialog(
                    self,
                    res['base_name'],
                    formats,
                    lambda ns: self.save_results(res, ns, is_final),
                    self.L.current_locale,
                    THEMES[self.CURR_THEME]
                )
            else:
                self.save_results(res, {}, is_final)
        
        if is_final:
            self.is_running = False
            self.current_worker = None
            self.btn_go.configure(
                text=self.T("start_btn"),
                fg_color=self.C("accent"),
                state="normal"
            )
    
    def save_results(self, res, names, is_final):
        """Sonuçları kaydeder."""
        try:
            out = Path(self.out_p.get())
            out.mkdir(parents=True, exist_ok=True)
            
            def f_t(s):
                """Zaman damgası formatlar."""
                ms = int((s % 1) * 1000)
                s = int(s)
                return f"{s//3600:02}:{(s%3600)//60:02}:{s%60:02},{ms:03}"
            
            format_map = {
                "sentence": (self.chk_ls, "srt"),
                "word": (self.chk_ws, "srt"),
                "json": (self.chk_js, "json"),
                "txt_flat": (self.chk_tx, "txt"),
                "txt_time": (self.chk_tt, "txt")
            }
            
            for k, (var, ext) in format_map.items():
                if var.get():
                    # Yerelleştirilmiş sonek (örn: _cumle)
                    default_suffix = self.T(f"suffix_{k}")
                    # Eğer çeviri yoksa fallback olarak ingilizce _k kullan
                    if default_suffix == f"suffix_{k}": default_suffix = f"_{k}"
                    
                    name = names.get(k, f"{res['base_name']}{default_suffix}")
                    path = get_unique_path(out / f"{name}.{ext}")
                    
                    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
                        if k == "sentence":
                            for i, s in enumerate(res['segments_s'], 1):
                                f.write(f"{i}\n{f_t(s['start'])} --> {f_t(s['end'])}\n{s['text']}\n\n")
                        
                        elif k == "word":
                            for i, w in enumerate(res['segments_w'], 1):
                                word_text = w.get('word', w.get('text', ''))
                                f.write(f"{i}\n{f_t(w['start'])} --> {f_t(w['end'])}\n{word_text}\n\n")
                        
                        elif k == "json":
                            import json as js
                            js.dump(res['raw'], f, ensure_ascii=False, indent=2)
                        
                        elif k == "txt_flat":
                            f.write(" ".join([s["text"].strip() for s in res['segments_s']]))
                        
                        elif k == "txt_time":
                            for s in res['segments_s']:
                                f.write(f"[{f_t(s['start'])}] {s['text'].strip()} [{f_t(s['end'])}]\n")
                    
                    self.log_q.put(f"   💾 OK: {Path(path).name}")
            
            if is_final and self.auto_o.get():
                subprocess.Popen(f'explorer "{out}"')
        
        except Exception as e:
            self.log_q.put(f"❌ Kayıt Hatası: {e}")
    
    # --- BACKGROUND TASKS ---
    
    def check_logs(self):
        """Log kuyruğunu kontrol eder."""
        try:
            while not self.log_q.empty():
                msg = self.log_q.get_nowait()
                self.log_box.insert('end', msg + "\n")
                self.log_box.see('end')
        except:
            pass
        self.after(100, self.check_logs)
    
    def check_results(self):
        """Sonuç kuyruğunu kontrol eder."""
        try:
            while not self.result_q.empty():
                msg = self.result_q.get_nowait()
                
                if msg["type"] == "progress":
                    self.p_bar.set(msg["value"])
                elif msg["type"] == "done":
                    self.done(msg["data"], msg["is_final"])
        except:
            pass
        self.after(100, self.check_results)
    
    def on_close(self):
        """Pencere kapatıldığında."""
        self.save_settings()
        
        if self.current_worker and self.current_worker.is_alive():
            self.current_worker.terminate()
            self.current_worker.join(timeout=0.1)
        
        self.destroy()
