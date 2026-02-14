"""
WHIXPI Pro V1.0 - Core Logic Engine
====================================
Miller Hybrid Splitter ve Chronos Timing algoritmaları.
Bu modül, AI çıktılarını profesyonel altyazı formatına dönüştürür.
"""

import textwrap


# =============================================================================
# CHRONOS TIMING ENGINE (v26.5)
# =============================================================================

def chronos_seamless_core(segments, threshold_sec, min_dur=0.2):
    """
    v26.5 Chronos Core: Seamless transition & duration guard.
    
    Segmentler arası boşlukları köprüler ve minimum süreyi garantiler.
    
    Args:
        segments: Segment listesi [{"start": float, "end": float, ...}, ...]
        threshold_sec: Bu değerden küçük boşluklar köprülenir (saniye)
        min_dur: Minimum segment süresi (saniye)
    
    Returns:
        İyileştirilmiş segment listesi
    """
    if not segments:
        return segments
    
    for i in range(len(segments) - 1):
        gap = segments[i+1]["start"] - segments[i]["end"]
        
        # 1. Zero-Gap Bridge: Küçük boşlukları kapat
        if gap <= threshold_sec:
            segments[i]["end"] = segments[i+1]["start"]
        
        # 2. Overlap Fixer: Örtüşmeleri düzelt
        if segments[i]["end"] > segments[i+1]["start"]:
            segments[i]["end"] = segments[i+1]["start"]

        # 3. Minimum Duration Guard: Minimum süreyi garantile
        if segments[i]["end"] - segments[i]["start"] < min_dur:
            segments[i]["end"] = segments[i]["start"] + min_dur
    
    # Son segment için de minimum süre kontrolü
    if segments[-1]["end"] - segments[-1]["start"] < min_dur:
        segments[-1]["end"] = segments[-1]["start"] + min_dur
    
    return segments


def waveform_finetune_chronos(segments):
    """
    v26.5 Chronos: Dynamic Gap Distribution & Shift.
    
    Kelimeler arası boşlukları dinamik olarak dağıtır.
    Segment sınırlarını kelime sınırlarına göre ayarlar.
    
    Args:
        segments: Segment listesi
    
    Returns:
        Rafine edilmiş segment listesi
    """
    refined_segments = []
    
    for seg in segments:
        if "words" not in seg or not seg["words"]:
            refined_segments.append(seg)
            continue
        
        words = seg["words"]
        
        for i in range(len(words) - 1):
            try:
                w1, w2 = words[i], words[i+1]
                gap = w2["start"] - w1["end"]
                
                if 0 < gap < 0.3:
                    # Dinamik dağıtım: %40-40 paylaştır, %20 emniyet
                    dist = min(gap * 0.4, 0.08)
                    w1["end"] += dist
                    w2["start"] -= dist
            except:
                pass
        
        # Segment sınırlarını rafine edilmiş kelimelere göre güncelle
        if words:
            seg["start"] = words[0]["start"]
            seg["end"] = words[-1]["end"]
        
        refined_segments.append(seg)
    
    return refined_segments


# =============================================================================
# MILLER HYBRID SPLITTER (v26)
# =============================================================================

def miller_hybrid_split(result, config):
    """
    v26 Miller Hybrid Architecture: Absolute Symmetry & Rhythmic Logic.
    
    AI çıktısını profesyonel, dengeli altyazı segmentlerine böler.
    
    Args:
        result: WhisperX aligned sonucu {"segments": [...]}
        config: Ayarlar dict'i {
            "max_words": int,      # Segment başına max kelime (0 = sınırsız)
            "max_lines": int,      # Segment başına max satır (0 = sınırsız)
            "base_limit": int      # Satır başına max karakter
        }
    
    Returns:
        Formatlanmış segment listesi [{"start", "end", "text"}, ...]
    """
    
    def safe_int(val, default=0):
        try:
            return int(str(val).strip()) if val else default
        except:
            return default
    
    mw = safe_int(config.get("max_words"), 0)
    ml = safe_int(config.get("max_lines"), 0)
    base_l = safe_int(config.get("base_limit"), 75)
    
    # Segment kapasitesi hesapla
    seg_capacity = (base_l * ml) if ml > 0 else 9999
    
    # Tüm kelimeleri düz listeye çıkar
    words = []
    for s in result.get("segments", []):
        for w in s.get("words", []):
            if "start" in w:
                words.append(w)
    
    # Eğer kelime yoksa veya sınır yoksa, orijinal segmentleri döndür
    if not words or (mw == 0 and ml == 0 and base_l == 0):
        return [
            {"start": s["start"], "end": s["end"], "text": s["text"].strip()} 
            for s in result.get("segments", [])
        ]
    
    # Bağlaçlar - satır başına düşmemeleri gerekir
    conjunctions = [
        "ve", "ama", "fakat", "çünkü", "veya", "lakin", "ancak",
        "and", "but", "or", "so", "because", "while"
    ]
    
    new_segs = []
    group = []
    
    def commit_group(grp):
        """Kelime grubunu segment olarak tamamla."""
        if not grp:
            return
        
        txt_content = " ".join([x.get("word", "") for x in grp]).strip()
        
        # --- MILLER BALANCING (v28 - Force Box Logic) ---
        if ml > 1:
            total_chars = len(txt_content)
            
            # İdeal satır sayısını belirle (Simetri için)
            target_lines = max(1, int(total_chars / base_l) + (1 if total_chars % base_l > (base_l * 0.1) else 0))
            target_lines = min(target_lines, ml)
            
            # Hedef genişlik: Metni mevcut satır sayısına bölecek en tatlı genişlik
            target_w = max(15, int(total_chars / target_lines))
            
            # 1. İlk Kesim (Tentative Wrap)
            lines = textwrap.wrap(txt_content, width=target_w + 5) # Esnek tolerans
            
            # 2. Hard Limit Enforcement (Duvar Kontrolü)
            # Eğer satır sayısı limiti aştıysa, alttan yukarı doğru birleştir.
            while len(lines) > ml:
                last = lines.pop()
                lines[-1] += " " + last
            
            # 3. Estetik Rötuşlar (Sadece çok satırlıysa)
            if len(lines) > 1:
                # A) Anti-Dangle (Tek kelime kalmasın)
                if len(lines[-1].split()) == 1:
                    prev_words = lines[-2].split()
                    if len(prev_words) > 1:
                        val = prev_words.pop()
                        # Eğer çok uzun bir kelime değilse aşağı at
                        if len(val) < 15:
                            lines[-1] = val + " " + lines[-1]
                            lines[-2] = " ".join(prev_words)
                
                # B) Bağlaç Koruması (Bağlaç satır sonunda kalmasın)
                for j in range(len(lines)-1):
                    l_w = lines[j].split()
                    if l_w:
                        last_word = l_w[-1]
                        clean_last = last_word.lower().strip(".,?!:;")
                        if clean_last in conjunctions:
                            # Bağlacı aşağı at
                            lines[j] = " ".join(l_w[:-1])
                            lines[j+1] = last_word + " " + lines[j+1]
            
            txt_content = "\n".join(lines)
        
        elif ml == 1:
            # Tek satır disiplini
            txt_content = "\n".join(textwrap.wrap(txt_content, width=base_l))
        
        new_segs.append({
            "start": grp[0]["start"], 
            "end": grp[-1]["end"], 
            "text": txt_content
        })
    
    # Kelimeleri segmentlere böl
    for w in words:
        if not group:
            group.append(w)
            continue
        
        last_text = group[-1].get("word", "").lower().strip(".,?!:;")
        split = False
        
        # 1. Sert Limit Check: Kelime Sayısı
        if mw > 0 and len(group) >= mw:
            split = True
        
        # 2. Sert Limit Check: Karakter Kapasitesi
        if not split and base_l > 0:
            current_len = sum(len(x.get("word", "")) for x in group) + len(group)
            
            # v26.1: Absolute Boundary Enforcement
            if current_len + len(w.get("word", "")) > seg_capacity:
                split = True
            
            # 3. Disiplinli Kesim: Noktalama & Bağlaç
            elif current_len >= (base_l * 0.7):
                if any(p in group[-1].get("word", "") for p in [".", "?", "!", ":"]):
                    split = True
                elif any(p in group[-1].get("word", "") for p in [",", ";"]) and current_len >= base_l:
                    split = True
        
        # 4. Sessizlik Yasası (Silence is Law)
        if not split:
            gap = w["start"] - group[-1]["end"]
            if gap > 0.5:
                split = True  # Yarım saniyelik nefes bölünür
            elif any(p in group[-1].get("word", "") for p in [".", "?", "!"]) and gap > 0.2:
                split = True
        
        if split:
            commit_group(group)
            group = [w]
        else:
            group.append(w)
    
    # Son grubu tamamla
    commit_group(group)
    
    # Segment geçişlerini düzelt
    for i in range(1, len(new_segs)):
        if new_segs[i]["start"] - new_segs[i-1]["end"] < 0.2:
            new_segs[i-1]["end"] = new_segs[i]["start"]
    
    return new_segs


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def format_timestamp(seconds):
    """
    Saniyeyi SRT zaman damgası formatına çevirir.
    
    Args:
        seconds: Zaman (float)
    
    Returns:
        "HH:MM:SS,mmm" formatında string
    """
    ms = int((seconds % 1) * 1000)
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
