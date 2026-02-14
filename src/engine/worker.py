"""
WHIXPI Pro V1.0 - Transcription Worker
=======================================
Arka planda çalışan AI transkripsiyon işçisi.
UI'ı dondurmadan tüm AI süreçlerini yönetir.
"""

import os
import sys
import gc
import time
import numpy as np
from pathlib import Path

import torch
import torch.multiprocessing as mp

# whisperx lazy import - çalışma zamanında yüklenir
whisperx = None

from src.engine.logic import (
    waveform_finetune_chronos,
    chronos_seamless_core,
    miller_hybrid_split
)


class TranscriptionWorker(mp.Process):
    """
    Multiprocessing tabanlı transkripsiyon işçisi.
    
    UI thread'ini engellemeden arka planda:
    - Whisper ile transkripsiyon
    - Wav2Vec2 ile hizalama
    - Chronos ile zamanlama iyileştirme
    - Miller Hybrid ile bölümleme
    işlemlerini gerçekleştirir.
    """
    
    def __init__(
        self, 
        audio_list, 
        out_dir, 
        config, 
        lang, 
        model_name, 
        log_q, 
        result_q, 
        locale_dict,
        vram_profile, 
        align_engine, 
        bridge_ms, 
        word_bridge_ms
    ):
        """
        Args:
            audio_list: İşlenecek ses/video dosyalarının yolları
            out_dir: Çıktı klasörü
            config: Ayarlar dict'i (max_words, max_lines, base_limit, vb.)
            lang: Dil kodu ("tr" veya "en")
            model_name: Whisper model adı ("large-v3")
            log_q: Log mesajları için multiprocessing.Queue
            result_q: Sonuçlar için multiprocessing.Queue
            locale_dict: Çeviri sözlüğü
            vram_profile: VRAM profili ("vram_sonic", "16gb_safe", vb.)
            align_engine: Hizalama motoru
            bridge_ms: Cümle köprüleme eşiği (ms)
            word_bridge_ms: Kelime köprüleme eşiği (ms)
            bridge_ms: Köprüleme süresi (ms)
            word_bridge_ms: Kelime köprüleme eşiği (ms)
        """
        super().__init__()
        
        self.audio_list = audio_list
        self.out_dir = out_dir
        self.config = config
        self.lang = lang
        self.model_name = model_name
        self.log_q = log_q
        self.result_q = result_q
        self.L = locale_dict
        self.vram_profile = vram_profile
        self.align_engine = align_engine
        self.bridge_ms = bridge_ms
        self.word_bridge_ms = word_bridge_ms
        self.stop_event = mp.Event()
        
        # VAD Cache Değişkenleri
        self._vad_model = None
        self._vad_utils = None
        self._vad_device = None
    
    def run(self):
        """Ana işlem döngüsü."""
        
        # Lazy import - whisperx sadece worker process'te yüklenir
        global whisperx
        import whisperx as wx
        whisperx = wx
        
        # --- EARLY FEEDBACK SYSTEM ---
        self.log_q.put("🚀 [OMEGA] Whixpi İşlem Merkezi Başlatıldı...")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.log_q.put(f"📡 Donanım Algılandı: [{device.upper()}]")
        
        total = len(self.audio_list)
        should_exit = False
        
        for idx, audio_path in enumerate(self.audio_list, 1):
            if self.stop_event.is_set() or should_exit:
                self.log_q.put(self.L.get("stopped", "İşlem durduruldu."))
                break
            
            file_success = False
            res_data = None
            
            try:
                # --- VRAM CONFIG ---
                v_prof = self.vram_profile
                v_map = {
                    # Sonic: Batch kullanıcıdan, Beam kullanıcıdan
                    "vram_sonic": (
                        int(self.config.get("batch_size", 32)), 
                        int(self.config.get("beam_size", 1)), 
                        "float16"
                    ),
                    # Custom: Batch kullanıcıdan, Beam kullanıcıdan
                    "vram_custom": (
                        int(self.config.get("batch_size", 8)), 
                        int(self.config.get("beam_size", 5)), 
                        "float16"
                    ),
                    "vram_ultra": (10, 20, "float16"),   # Eski 16GB Safe
                    "vram_high": (10, 10, "float16"),    # Eski 12GB
                    "vram_mid": (6, 5, "int8"),          # Eski 8GB
                    "vram_eko": (1, 1, "int8")           # Eski 4GB
                }
                # Fallback: Batch 4, Beam 5 (vram_prof tanınmazsa)
                batch_size, b_size, compute_type = v_map.get(v_prof, (4, 5, "float16"))
                
                # Proactive Flush
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                self.log_q.put(f"   ⚙️ VRAM Planı: [Oda: {v_prof} | Batch: {batch_size} | Beam: {b_size}]")
                
                base_name = Path(audio_path).stem
                self.log_q.put(
                    self.L.get("trans_start", "🚀 [{}/{}] Transkripsiyon ({}): {}")
                    .format(idx, total, self.lang.upper(), base_name)
                )
                
                if self.stop_event.is_set():
                    should_exit = True
                    continue
                
                # Load Audio
                audio_data = whisperx.load_audio(audio_path)
                
                # --- STEP 1: TRANSCRIBE ---
                self.log_q.put("   📦 AI Motoru Hazırlanıyor (Large v3)... Lütfen Bekleyin.")
                
                if self.stop_event.is_set():
                    should_exit = True
                    continue
                
                asr_options = {"beam_size": b_size}
                
                # --- FIX: EXE Path ---
                if getattr(sys, 'frozen', False):
                    # EXE modunda: EXE'nin oldugu klasor
                    base_path = os.path.dirname(sys.executable)
                else:
                    # Script modunda: Proje kok dizini
                    base_path = os.getcwd()
                
                # Yerel model kontrolü
                local_model_path = os.path.join(base_path, "models", "large-v3")
                model_to_load = self.model_name
                
                if not os.path.exists(local_model_path):
                    self.log_q.put("   🌐 Model İndiriliyor... (Bu işlem bir seferliktir, yaklaşık 3.1 GB)")
                    try:
                        import threading
                        from huggingface_hub import snapshot_download
                        
                        total_size_gb = 3.09 # large-v3 yaklaşık boyutu
                        stop_monitor = threading.Event()
                        
                        def monitor_progress():
                            last_size = 0
                            start_time = time.time()
                            while not stop_monitor.is_set():
                                try:
                                    current_size = sum(f.stat().st_size for f in Path(local_model_path).rglob('*') if f.is_file())
                                    current_gb = current_size / (1024**3)
                                    percent = (current_gb / total_size_gb) * 100
                                    
                                    # Hız hesapla
                                    elapsed = time.time() - start_time
                                    if elapsed > 0:
                                        speed = (current_size - last_size) / (1024**2) # MB/s
                                        if speed > 0:
                                            self.log_q.put(f"   📥 İndiriliyor: {current_gb:.2f} GB / {total_size_gb} GB [%{int(percent)}] | Hız: {speed:.1f} MB/s")
                                    
                                    last_size = current_size
                                    start_time = time.time()
                                except: pass
                                time.sleep(2) # 2 saniyede bir guncelle

                        # Monitoru baslat
                        monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
                        if not os.path.exists(local_model_path): os.makedirs(local_model_path, exist_ok=True)
                        monitor_thread.start()

                        # Asıl indirme
                        snapshot_download(
                            repo_id="Systran/faster-whisper-large-v3",
                            local_dir=local_model_path,
                            local_dir_use_symlinks=False,
                            resume_download=True
                        )
                        
                        stop_monitor.set() # Izlemeyi durdur
                        self.log_q.put("   ✅ Model başarıyla yerel klasöre indirildi.")
                    except Exception as e:
                        self.log_q.put(f"   ⚠️ İndirme sisteminde hata: {e}")

                if os.path.exists(local_model_path):
                    self.log_q.put(f"   📂 Yerel Model Aktif: {local_model_path}")
                    model_to_load = local_model_path

                model = whisperx.load_model(
                    model_to_load, 
                    device, 
                    compute_type=compute_type,
                    language=self.lang, 
                    asr_options=asr_options
                )
                result = model.transcribe(audio_data, batch_size=batch_size)
                
                if self.stop_event.is_set():
                    del model
                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    should_exit = True
                    continue
                
                self.log_q.put("   🧹 VRAM Arındırıldı, sıradaki adıma geçiliyor.")
                del model
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                if self.stop_event.is_set():
                    should_exit = True
                    continue
                
                self.result_q.put({"type": "progress", "value": 0.4})
                
                # --- STEP 2: ALIGNMENT ---
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                self.log_q.put(self.L.get("step_align", "   2/4 Hizalama..."))
                
                if self.stop_event.is_set():
                    should_exit = True
                    continue
                
                # Türkçe için özel alignment modeli
                align_model_name = (
                    "ozcangundes/wav2vec2-large-xlsr-53-turkish" 
                    if self.lang == "tr" else None
                )
                
                model_a, metadata = whisperx.load_align_model(
                    language_code=self.lang, 
                    device=device, 
                    model_name=align_model_name
                )
                aligned = whisperx.align(
                    result["segments"], 
                    model_a, 
                    metadata, 
                    audio_data, 
                    device, 
                    return_char_alignments=False
                )
                
                del model_a
                gc.collect()
                if device == "cuda":
                    torch.cuda.empty_cache()
                
                self.result_q.put({"type": "progress", "value": 0.7})
                
                # --- STEP 3: CHRONOS TIMING ---
                self.log_q.put(self.L.get("step_wave", "   3/4 Akıllı Köprüleme..."))
                
                # 1. Waveform Finetune (Sadece köprüleme aktifse uygulanır)
                if self.bridge_ms > 0 or self.word_bridge_ms > 0:
                    aligned["segments"] = waveform_finetune_chronos(aligned["segments"])
                
                # 2. Diamond Refinery (Optional)
                # 2. Diamond Refinery (ALWAYS ON - STANDARD)
                # Artık opsiyonel değil, standart prosedür.
                self.log_q.put(f"   💎 Chronos VAD Refinery: Auto-Pilot Active")
                
                # Sentence level refinery
                aligned["segments"] = self.diamond_refinery(
                    aligned["segments"], 
                    audio_data, 
                    mode="sentence"
                )
                    
                # Word level refinery (Global Batch Optimization)
                all_words = []
                for s in aligned["segments"]:
                    if "words" in s:
                        all_words.extend(s["words"])
                
                if all_words:
                    self.log_q.put(f"   💎 Kelime Analizi: {len(all_words)} kelime tek seferde işleniyor...")
                    refined_words = self.diamond_refinery(all_words, audio_data, mode="word")
                    
                    # Dağıtım
                    curr = 0
                    for s in aligned["segments"]:
                        if "words" in s:
                            count = len(s["words"])
                            s["words"] = refined_words[curr : curr+count]
                            curr += count
                
                # --- STEP 4: SMART SPLIT ---
                self.log_q.put(self.L.get("step_fmt", "   4/4 Akıllı Formatlama..."))
                
                segments_s = miller_hybrid_split(aligned, self.config)
                
                # Sentence level seamless bridge
                if self.bridge_ms > 0:
                    segments_s = chronos_seamless_core(
                        segments_s, 
                        self.bridge_ms / 1000.0, 
                        min_dur=0.2
                    )
                
                # Word-Based Segment Collection
                segments_w = []
                for s in aligned["segments"]:
                    for w in s.get("words", []):
                        if "start" in w:
                            segments_w.append(w)
                
                # Word level seamless bridge
                if self.word_bridge_ms > 0 and segments_w:
                    segments_w = chronos_seamless_core(
                        segments_w, 
                        self.word_bridge_ms / 1000.0, 
                        min_dur=0.08
                    )
                
                res_data = {
                    "base_name": Path(audio_path).stem,
                    "segments_s": segments_s,
                    "segments_w": segments_w,
                    "raw": aligned
                }
                file_success = True
                
                # Memory Cleanup
                del audio_data, result
                gc.collect()
                if device == "cuda":
                    torch.cuda.empty_cache()
                
                if self.stop_event.is_set():
                    should_exit = True
                    continue
                
                time.sleep(0.01)
            
            except Exception as e:
                self.log_q.put(
                    self.L.get("error_file", "❌ HATA [{}]: {}")
                    .format(Path(audio_path).name, str(e))
                )
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                file_success = False
            
            finally:
                # Durdurulmuşsa işaretle (return yerine flag kullan)
                if self.stop_event.is_set():
                    self.log_q.put(self.L.get("stopped", "İşlem durduruldu."))
                    self.result_q.put({"type": "done", "data": None, "is_final": True})
                    should_exit = True
                elif file_success:
                    self.result_q.put({
                        "type": "done", 
                        "data": res_data, 
                        "is_final": (idx == total)
                    })
                elif idx == total:
                    self.result_q.put({"type": "done", "data": None, "is_final": True})
        
        if not should_exit:
            self.result_q.put({"type": "progress", "value": 1.0})
            self.log_q.put(self.L.get("all_done", "🏁 TÜM İŞLEMLER TAMAMLANDI!"))
    
    def analyze_vad_params(self, audio_np):
        """
        Ses dosyasının karakteristiğine göre ideal VAD parametrelerini hesaplar.
        UI'sız, arka planda çalışan 'Akıllı Analiz' sistemi.
        """
        try:
            # 1. Gürültü Tabanı (Noise Floor) Analizi
            # Sesi 50ms'lik pencerelere bölüp en sessiz %10'luk kısmın enerjisine bakıyoruz.
            chunk_n = int(16000 * 0.05)
            # Hız için %1'lik örneklem (stride) alıyoruz
            stride = max(1, len(audio_np) // 1000)
            samples = np.abs(audio_np[::stride])
            
            # Alt %10 (Noise) ve Üst %10 (Speech) Enerjisi
            sorted_energy = np.sort(samples)
            noise_level = np.mean(sorted_energy[:int(len(sorted_energy)*0.1)])
            speech_level = np.mean(sorted_energy[-int(len(sorted_energy)*0.1):])
            
            # Dinamik Aralık (Speech / Noise Ratio)
            snr = speech_level / (noise_level + 1e-9)
            
            # --- PARAMETRE HESAPLAMA (SABİT AGRESIF PRESET) ---
            # Kullanıcı geri bildirimine göre başlangıç gecikmelerini (Late Attack) önlemek için:
            # 1. Threshold ÇOK DÜŞÜK (0.08) -> Fısıltıları ve başlangıç nefeslerini yakala.
            # 2. Pad Start ÇOK YÜKSEK (0.5s) -> Kelimeden yarım saniye öncesini de al.
            
            threshold = 0.08
            pad_start = 0.50
            pad_end = 0.50
            min_silence = 0.50
            
            self.log_q.put(f"   🧠 Smart VAD: [FIXED] Thr={threshold} | Pad={pad_start}/{pad_end}s | Attack=AGGRESSIVE")
            return threshold, pad_start, pad_end, min_silence
            
        except Exception as e:
            print(f"Smart VAD Error: {e}")
            return 0.15, 0.1, 0.2, 0.4
    
    def get_vad_model(self):
        """VAD Modelini Cache'ten getir veya yükle (Tek Seferlik Yük)"""
        if hasattr(self, '_vad_model') and self._vad_model is not None:
            return self._vad_model, getattr(self, '_vad_utils', None)

        try:
            self.log_q.put("   ⏳ VAD Modeli İlk Kez Yükleniyor... (Bir kerelik işlem)")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', 
                                        force_reload=False, trust_repo=True, verbose=False)
            model = model.to(device)
            self._vad_model = model
            self._vad_utils = utils
            self._vad_device = device
            return model, utils
        except Exception as e:
            self.log_q.put(f"⚠️ VAD Model Yükleme Hatası: {e}")
            return None, None

    def diamond_refinery(self, segments, audio_np, mode="sentence"):
        """Diamond Precision v7.0 (Fast + Vectorized + Cached + Auto-Pilot)"""
        import time
        t_start = time.time()
        
        try:
            model_v, utils = self.get_vad_model()
            if model_v is None: return segments
            
            device = self._vad_device
            sr = 16000
            
            # --- SMART VAD ANALIZI ---
            # Kullanıcıdan bağımsız, her dosyaya özel ayarlar
            dyn_thresh, dyn_pad_s, dyn_pad_e, dyn_min_sil = self.analyze_vad_params(audio_np)
            
            # Threshold Override - TAM OTOMATİK
            # Kullanıcı hassasiyeti kalktı. Direkt Smart VAD değerini kullanıyoruz.
            vad_threshold = dyn_thresh
            
            # --- ZAMANLAMA BAŞLANGICI (HATA DÜZELTME) ---
            t_infer_start = time.time()
            
            audio_t = torch.from_numpy(audio_np).to(device)
            v_prof = self.vram_profile
            
            # Smart Batch Sizing
            # Smart Batch Sizing
            if "vram_eko" in v_prof: meta_batch = 2000
            elif "vram_mid" in v_prof: meta_batch = 10000
            elif "vram_ultra" in v_prof or "vram_sonic" in v_prof or "vram_custom" in v_prof: meta_batch = 40000
            else: meta_batch = 20000 # vram_high ve default
            
            chunk_size = 512
            
            # Padding
            flat_len = len(audio_t)
            pad_needed = chunk_size - (flat_len % chunk_size)
            if pad_needed != chunk_size:
                audio_t = torch.nn.functional.pad(audio_t, (0, pad_needed))
            
            batched_audio = audio_t.view(-1, chunk_size)
            global_probs = []
            
            model_v.eval()
            with torch.no_grad():
                for i in range(0, len(batched_audio), meta_batch):
                    if self.stop_event.is_set(): return segments
                    b = batched_audio[i:i+meta_batch]
                    out = model_v(b, sr)
                    if out.dim() > 1 and out.shape[-1] > 1:
                         global_probs.append(out[:, 1].cpu())
                    else:
                         global_probs.append(out.view(-1).cpu())
            
            full_map = torch.cat(global_probs).numpy()
            t_infer_end = time.time()
            
            # --- CPU SOLVER (Vectorized & Smart) ---
            t_solve_start = time.time()
            
            seg_count = len(segments)
            starts = np.array([s["start"] for s in segments])
            ends = np.array([s["end"] for s in segments])
            
            # Smart Padding Uygulaması
            # VAD'ın bulduğu sınırları biraz esnetiyoruz (Nefes payı)
            SAFETY = 0.02
            prev_ends = np.concatenate(([0], ends[:-1] + SAFETY))
            next_starts = np.concatenate((starts[1:] - SAFETY, [len(audio_np)/sr]))
            
            # Dinamik Padding Değerleri Kullanılıyor
            w_starts = np.maximum(prev_ends, starts - dyn_pad_s)
            w_ends = np.minimum(next_starts, ends + dyn_pad_e)
            
            idx_starts = (w_starts * sr / 512).astype(int)
            idx_ends = (w_ends * sr / 512).astype(int)
            idx_starts = np.clip(idx_starts, 0, len(full_map))
            idx_ends = np.clip(idx_ends, 0, len(full_map))
            
            # Window Analysis (Genişletilmiş Tolerans - V10 Klasik Ayarı)
            MAX_S_DRIFT = 0.30 if mode == "sentence" else 0.15 # Başlangıçta esneklik (Efendim sorunu için)
            MAX_E_DRIFT = dyn_min_sil # Bitişte esneklik (Smart Analysis'ten gelen)
            SNAP_WIN = 1200 
            
            for i in range(seg_count):
                s_idx, e_idx = idx_starts[i], idx_ends[i]
                if s_idx >= e_idx: continue
                
                local_probs = full_map[s_idx:e_idx]
                hits = np.where(local_probs > vad_threshold)[0]
                
                if hits.size > 0:
                    first_hit = s_idx + hits[0]
                    last_hit = s_idx + hits[-1]
                    
                    raw_s = first_hit * 512
                    raw_e = (last_hit * 512) + 512
                    
                    # Zero Crossing Snap
                    sw1 = max(0, raw_s - SNAP_WIN)
                    ew1 = min(len(audio_np), raw_s + SNAP_WIN)
                    if ew1 > sw1: snap_s = sw1 + np.argmin(np.abs(audio_np[sw1:ew1]))
                    else: snap_s = raw_s
                    
                    sw2 = max(0, raw_e - SNAP_WIN)
                    ew2 = min(len(audio_np), raw_e + SNAP_WIN)
                    if ew2 > sw2: snap_e = sw2 + np.argmin(np.abs(audio_np[sw2:ew2]))
                    else: snap_e = raw_e
                    
                    cand_s = snap_s / sr
                    cand_e = (snap_e / sr) + 0.04
                    
                    if abs(cand_s - starts[i]) < MAX_S_DRIFT:
                        segments[i]["start"] = round(max(prev_ends[i], cand_s), 3)
                    if abs(cand_e - ends[i]) < MAX_E_DRIFT:
                        segments[i]["end"] = round(min(next_starts[i] - 0.01, cand_e), 3)
                
                if segments[i]["end"] <= segments[i]["start"]: 
                    segments[i]["end"] = segments[i]["start"] + 0.1
            
            t_total = time.time() - t_start
            self.log_q.put(f"   ⏱️ VAD Analiz: {t_total:.2f}s (GPU: {t_infer_end-t_infer_start:.2f}s)")
            
            del batched_audio; del full_map; del audio_t
            gc.collect(); torch.cuda.empty_cache()
            return segments

        except Exception as e:
            print(f"Diamond Error: {e}")
            self.log_q.put(f"⚠️ VAD Hatası: {str(e)[:50]}")
            return segments
