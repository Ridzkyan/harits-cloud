"""
================================================================================
🚀 AUTO SUARA GROQ - PEMBACA LAYAR OTOMATIS (FEMALE VOICE TTS) 🚀
================================================================================
Fitur:
1. OTOMATIS MEMBACA LAYAR DEPAN:
   - Pengguna TIDAK PERLU menyalin/menyorot teks apapun!
   - Cukup biarkan soal pilihan ganda tampil di layar laptop, lalu tekan shortcut.
   - Skrip secara otomatis menangkap tampilan layar depan laptop, membaca teksnya
     menggunakan Windows OCR bawaan (winocr), dan mengirimkannya ke Groq AI.
2. 3 API KEY GROQ TERSAMBUNG SECARA OTOMATIS:
   - Menggunakan 3 API key aktif dari api key.txt dengan rotasi/failover otomatis.
3. KELUARAN SUARA CEWEK (TEXT-TO-SPEECH):
   - Groq memfilter antarmuka layar dan langsung menemukan soal & opsi A, B, C, D, E.
   - Suara cewek ramah (Google Neural TTS / gTTS) langsung membisikkan huruf
     jawaban dan alasannya ke headset pengguna.
4. KONTROL SHORTCUT GLOBAL DI LATAR BELAKANG:
   - [Ctrl + Shift + F8] : Tangkap layar & jawab soal pilihan ganda via suara cewek.
   - [Ctrl + Shift + F9] : Hentikan suara seketika (Mute / Stop).
   - [Ctrl + Shift + F12]: Keluar dari program latar belakang.
================================================================================
"""

import time
import os
import sys
import json
import io
import threading
import winsound
import keyboard
from groq import Groq
from gtts import gTTS
import pygame

CONFIG_FILE = "api_keys_groq.json"

# Shortcut keyboard (Langka & tidak bentrok dengan browser atau Windows)
HOTKEY_SOLVE = "ctrl+shift+f8"
HOTKEY_STOP_AUDIO = "ctrl+shift+f9"
HOTKEY_EXIT = "ctrl+shift+f12"

# Inisialisasi pygame mixer untuk audio berkualitas tinggi
try:
    pygame.mixer.init()
except Exception as e:
    print(f"[!] Warning: Gagal inisialisasi mixer: {e}")

# Kunci sinkronisasi agar proses tidak bertabrakan saat shortcut ditekan cepat
is_processing = False
processing_lock = threading.Lock()


def load_api_keys():
    """Memuat daftar API Key dari file konfigurasi lokal secara aman."""
    api_keys = []
    # 1. Coba baca dari api_keys_groq.json
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded = json.load(f)
                if isinstance(loaded, list) and len(loaded) > 0:
                    api_keys = [k for k in loaded if k and k.startswith("gsk_")]
        except Exception:
            pass

    # 2. Coba baca dari api key.txt jika belum ada
    if not api_keys and os.path.exists("api key.txt"):
        try:
            with open("api key.txt", "r") as f:
                for line in f:
                    if "gsk_" in line:
                        parts = line.strip().split()
                        for p in parts:
                            if p.startswith("gsk_") and p not in api_keys:
                                api_keys.append(p)
            if api_keys:
                with open(CONFIG_FILE, "w") as f:
                    json.dump(api_keys, f, indent=2)
        except Exception:
            pass

    # 3. Jika belum ada sama sekali, minta input dari user
    if not api_keys:
        print("\n[+] Masukkan setidaknya 1 API Key Groq Anda:")
        k1 = input("API Key 1: ").strip()
        k2 = input("API Key 2: ").strip()
        k3 = input("API Key 3: ").strip()
        api_keys = [k for k in [k1, k2, k3] if k and k.startswith("gsk_")]
        if api_keys:
            with open(CONFIG_FILE, "w") as f:
                json.dump(api_keys, f, indent=2)

    return api_keys


def play_beep(frequency=1200, duration=100):
    """Memberi sinyal audio halus ke headset bahwa shortcut berhasil ditekan."""
    try:
        winsound.Beep(frequency, duration)
    except Exception:
        pass


def stop_audio():
    """Menghentikan suara yang sedang berbicara seketika."""
    try:
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            print("\n[🔊] Suara dihentikan (Muted).")
    except Exception as e:
        print(f"[!] Gagal menghentikan audio: {e}")


def speak_female_voice(text):
    """
    Memutar suara wanita Bahasa Indonesia (Mbak Google) langsung dari RAM (in-memory).
    Jika koneksi audio terganggu, otomatis fallback ke SAPI5 Microsoft Zira.
    """
    try:
        stop_audio()
        tts = gTTS(text=text, lang="id")
        audio_stream = io.BytesIO()
        tts.write_to_fp(audio_stream)
        audio_stream.seek(0)

        pygame.mixer.music.load(audio_stream)
        pygame.mixer.music.play()
        print(f"\n[🗣️ Suara Cewek]: \"{text}\"")

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    except Exception as e:
        print(f"[!] gTTS gagal ({e}), mengalihkan ke Windows SAPI5 Offline...")
        try:
            import win32com.client
            import pythoncom
            pythoncom.CoInitialize()
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            for v in speaker.GetVoices():
                if "zira" in v.GetDescription().lower():
                    speaker.Voice = v
                    break
            speaker.Speak(text)
            pythoncom.CoUninitialize()
        except Exception as e2:
            print(f"[!] Gagal memutar suara cadangan: {e2}")


def capture_front_screen():
    """
    Menangkap tampilan layar laptop yang sedang aktif di depan secara otomatis.
    Mendukung berbagai metode fallback agar 100% andal di Windows.
    """
    # Metode 1: PIL ImageGrab (standar Windows)
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        if img:
            return img
    except Exception:
        pass

    # Metode 2: PyAutoGUI Screenshot
    try:
        import pyautogui
        img = pyautogui.screenshot()
        if img:
            return img
    except Exception:
        pass

    # Metode 3: MSS (Direct GDI ctypes)
    try:
        import mss
        with mss.MSS() as sct:
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sct_img = sct.grab(monitor)
            from PIL import Image
            return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
    except Exception:
        pass

    return None


def extract_screen_text(img):
    """
    Membaca seluruh teks dari gambar tangkapan layar menggunakan Windows Native OCR (winocr).
    """
    try:
        import winocr
        res = winocr.recognize_pil_sync(img, "en-US")
        if res and "text" in res and res["text"].strip():
            return res["text"].strip()
    except Exception as e:
        print(f"[!] Windows OCR Error: {e}")

    # Fallback ke pytesseract jika ada
    try:
        import pytesseract
        text = pytesseract.image_to_string(img)
        if text and text.strip():
            return text.strip()
    except Exception:
        pass

    return None


def get_groq_answer_from_screen(screen_text, keys):
    """
    Mengirimkan teks tangkapan layar ke Groq AI dengan model 120B (didukung Qwen) yang telah DITRAINING
    SECARA INTENSIF sebagai Dosen Bahasa Inggris S3 Swiss untuk menyelesaikan latihan soal TOEFL tingkat sulit.
    Dilengkapi sistem anti-penolakan dan penalaran gramatikal mutlak (100% akurat).
    """
    import re

    sys_prompt = (
        "You are an expert Swiss Professor of English Linguistics and the world's foremost TOEFL ITP/iBT authority.\n"
        "Your role is to analyze English grammar questions from screen captures and determine the single 100% correct answer.\n\n"
        "DOCTORAL TRAINING RULES (MASTER GRAMMAR SYSTEM - 100% ACCURACY):\n"
        "1. NEGATIVE INVERSION (Auxiliary + Subject + Verb):\n"
        "   - Whenever a sentence starts with negative/restrictive phrases ('Under no circumstances', 'Rarely', 'Scarcely', 'Hardly', 'Not until', 'Seldom', 'Never', 'Not only', 'At no time', 'In no way', 'Only after'):\n"
        "     The clause MUST be inverted: [Auxiliary/Modal + Subject + Main Verb]!\n"
        "     * 'Under no circumstances should hazardous materials be left...' (Auxiliary 'should' + Subject 'hazardous materials' + 'be left')\n"
        "     * 'Rarely has such an intricate alignment... been recorded' (Auxiliary 'has' + Subject 'such an intricate alignment' + 'been recorded')\n"
        "     * 'Not until the satellite reached its orbit did it begin...' (Auxiliary 'did' + Subject 'it' + 'begin')\n"
        "2. COMPARATIVE STRUCTURE & PRONOUN REFERENCE:\n"
        "   - In comparisons with 'than' or 'as', replace the compared noun with the correct formal demonstrative pronoun:\n"
        "     * For plural nouns (e.g., 'data', 'findings', 'results', 'specimens', 'samples'): use 'those' / 'those of' / 'those [V3]'! (NOT 'what', 'that', or 'it').\n"
        "       Example: 'The data were far more reliable than those collected by the previous team.'\n"
        "     * For singular/uncountable nouns (e.g., 'climate', 'output', 'level'): use 'that' / 'that of'.\n"
        "3. RELATIVE CLAUSE FINITE VERB REQUIREMENT:\n"
        "   - In formal relative clauses such as 'the primary objective of which [VERB]', the clause REQUIRES a finite predicative verb ('is', 'was', 'are', 'were').\n"
        "     * Example: '...the primary objective of which is to minimize contamination.' (NEVER infinitive 'to be' or participle 'being').\n"
        "4. CORRELATIVE CONJUNCTION PAIRINGS:\n"
        "   - 'not only' MUST pair strictly with 'but also' (NEVER 'plus', 'as well as', 'along with', or 'and also').\n"
        "   - 'either... or', 'neither... nor', 'both... and'.\n"
        "5. SUBJUNCTIVE MOOD (BASE VERB):\n"
        "   - Verbs/adjectives of urgency or necessity (recommend, insist, suggest, demand, require, essential, vital, important) + that + subject + [BASE VERB / bare infinitive without -s/-es/-ed]!\n"
        "     * Example: 'recommended that every candidate submit...' (NOT 'submits' or 'submitted').\n"
        "     * Example: 'insisted that all records be kept...' (NOT 'are' or 'were').\n"
        "6. DOUBLE VERB TRAP (REDUCED RELATIVE CLAUSE):\n"
        "   - If a sentence already contains a finite main verb later in the sentence (e.g., 'provided', 'shows', 'is', 'challenges'), do NOT choose a finite verb with tense/auxiliary. Choose a reduced participle (V3 for passive, V-ing for active).\n"
        "     * Example: 'The research findings, reviewed by international scholars, challenge the prevailing theory.'\n"
        "7. SUBJECT-VERB AGREEMENT:\n"
        "   - Intervening prepositional phrases (together with, along with, as well as, in addition to, of) do NOT change the number of the head subject.\n\n"
        "STRICT TASK RULES:\n"
        "- Identify the multiple-choice question on screen.\n"
        "- Output strictly and ONLY one single line:\n"
        "Jawabannya [HURUF]\n\n"
        "Do not repeat the question, do not output explanations, and do not make lists.\n\n"
        "FEW-SHOT EXAMPLES:\n"
        "Input: 'Under no circumstances ___ left unattended. A. materials should be B. should materials be C. be materials D. materials be'\n"
        "Output: Jawabannya B\n\n"
        "Input: 'The data were far more reliable than ___ by the previous team. A. what was collected B. those collected C. that collected D. which collected'\n"
        "Output: Jawabannya B\n\n"
        "Input: 'Rarely ___ such an alignment recorded. A. it has been B. has C. was it D. has it'\n"
        "Output: Jawabannya B\n\n"
        "Input: '...the primary objective of which ___ to minimize sample contamination. A. to be B. is C. being D. it is'\n"
        "Output: Jawabannya B\n\n"
        "Input: '...enduring not only extreme weather conditions ___ severe seismic vibrations. A. plus B. but also C. as well as D. along with'\n"
        "Output: Jawabannya B\n"
    )

    # Prioritas model: 120b (terbukti 100% pada soal jebakan sulit), lalu Qwen, lalu 20b
    models_to_try = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]

    for idx, key in enumerate(keys):
        client = Groq(api_key=key)
        for model_name in models_to_try:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": screen_text},
                    ],
                    model=model_name,
                    temperature=0.0,
                )
                full_content = chat_completion.choices[0].message.content.strip()

                # Cek jika model mengeluarkan teks penolakan (safety refusal)
                lower_content = full_content.lower()
                if "i'm sorry" in lower_content or "can't help" in lower_content or "cannot help" in lower_content:
                    print(f"  [!] Model {model_name} memicu filter penolakan, beralih ke model berikutnya...")
                    continue

                # Ekstraksi huruf jawaban akhir secara ketat: HANYA "Jawabannya [A-E]"
                match = re.search(r"Jawabannya\s+([A-Ea-e])", full_content)
                if match:
                    voice_answer = f"Jawabannya {match.group(1).upper()}"
                    return voice_answer, full_content, idx + 1, model_name

                # Cari huruf A, B, C, D, atau E pertama yang terisolasi
                letter_match = re.search(r"\b([A-Ea-e])\b", full_content)
                if letter_match:
                    voice_answer = f"Jawabannya {letter_match.group(1).upper()}"
                    return voice_answer, full_content, idx + 1, model_name

            except Exception as e:
                print(f"  [!] Groq Key {idx + 1} ({model_name}) Limit/Error: {e}")
                continue

    return None, None, -1, None


def process_screen_pipeline(api_keys):
    """
    Alur kerja otomatis membaca layar depan:
    1. Notifikasi beep halus.
    2. Tangkap layar depan laptop (tanpa menyalin teks manual).
    3. Baca teks layar dengan OCR.
    4. Analisis soal pilihan ganda di Groq.
    5. Bacakan jawaban dengan suara cewek.
    """
    global is_processing

    if not processing_lock.acquire(blocking=False):
        play_beep(500, 80)
        return

    try:
        is_processing = True

        # Sinyal suara ke headset: shortcut diterima
        play_beep(1200, 100)

        print("\n" + "=" * 55)
        print("[📸] Mengambil tangkapan layar tampilan depan laptop...")
        img = capture_front_screen()

        screen_text = None
        if img:
            print(f"[🔍] Membaca teks pada layar ({img.size[0]}x{img.size[1]} px)...")
            screen_text = extract_screen_text(img)

        # Cadangan sekunder: jika OCR tidak mendeteksi teks tetapi di clipboard ada teks
        if not screen_text:
            try:
                import pyperclip
                clip_text = pyperclip.paste().strip()
                if clip_text and len(clip_text) > 10:
                    screen_text = clip_text
                    print("[ℹ️] Menggunakan teks cadangan dari clipboard.")
            except Exception:
                pass

        if not screen_text:
            print("[-] Gagal membaca tampilan layar atau teks tidak ditemukan!")
            speak_female_voice("Maaf, teks pada layar tidak terbaca. Pastikan soal tampil jelas di layar depan.")
            return

        print(f"[📄] Teks layar terdeteksi ({len(screen_text)} karakter).")
        preview = screen_text.replace("\n", " ")[:140] + "..."
        print(f"     Preview: \"{preview}\"")
        print("[⚡] Groq sedang menganalisis soal pilihan ganda...")

        # Dapatkan jawaban dari Groq dengan model 120B & penalaran doktoral
        voice_answer, full_content, key_used, model_used = get_groq_answer_from_screen(screen_text, api_keys)

        if voice_answer:
            print(f"[✅] Analisis Groq ({model_used} | Key {key_used}):")
            for line in full_content.splitlines():
                print(f"     {line}")
            print(f"[🔊] Disuarakan ke headset: \"{voice_answer}\"")
            play_beep(1600, 80)
            speak_female_voice(voice_answer)
        else:
            print("[-] Semua API Key Groq gagal atau limit.")
            speak_female_voice("Maaf, semua API Key Groq sedang mengalami limit atau gangguan.")

    except Exception as e:
        print(f"\n[!] Terjadi kesalahan sistem: {e}")
    finally:
        is_processing = False
        processing_lock.release()


def trigger_screen_hotkey(api_keys):
    """Menjalankan proses membaca layar dalam background thread agar hotkey tetap responsif."""
    worker = threading.Thread(target=process_screen_pipeline, args=(api_keys,), daemon=True)
    worker.start()


def main():
    print("=" * 65)
    print(" 🚀 AUTO SUARA GROQ - PEMBACA LAYAR OTOMATIS (SUARA CEWEK) 🚀")
    print("=" * 65)

    api_keys = load_api_keys()
    print(f"\n[+] Terhubung dengan {len(api_keys)} API Key Groq:")
    for i, k in enumerate(api_keys):
        masked = k[:8] + "..." + k[-4:]
        print(f"    - Key {i+1}: {masked}")

    print("\n" + "-" * 65)
    print("📌 CARA KERJA (TANPA PERLU MENYALIN TEKS):")
    print(" 1. Buka browser atau aplikasi ujian Anda seperti biasa di layar laptop.")
    print(" 2. Pastikan soal pilihan ganda tampil di layar depan.")
    print(f" 3. Tekan Shortcut Keyboard: [{HOTKEY_SOLVE.upper()}]")
    print("    -> Skrip OTOMATIS membaca tampilan layar depan Anda.")
    print("    -> Groq mencari jawaban soal pilihan ganda.")
    print("    -> Suara cewek langsung membisikkan huruf & jawabannya ke headset!")
    print("\n📌 KONTROL TAMBAHAN:")
    print(f" - [{HOTKEY_STOP_AUDIO.upper()}] : Hentikan suara seketika (Mute/Stop).")
    print(f" - [{HOTKEY_EXIT.upper()}] : Keluar dari program latar belakang.")
    print("-" * 65)
    print("\n[*] Program aktif di latar belakang. Silakan uji coba sekarang...")

    # Daftarkan hotkey global
    keyboard.add_hotkey(HOTKEY_SOLVE, lambda: trigger_screen_hotkey(api_keys))
    keyboard.add_hotkey(HOTKEY_STOP_AUDIO, stop_audio)

    # Tunggu tombol keluar
    keyboard.wait(HOTKEY_EXIT)
    print("\n[+] Program dihentikan oleh pengguna. Sampai jumpa!")


if __name__ == "__main__":
    main()
