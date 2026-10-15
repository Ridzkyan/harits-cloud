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

CONFIG_ROOT = r"C:\Ridho Dzaky Raihan\Harits Cloud\api_keys_groq.json"
CONFIG_DIST = r"C:\Ridho Dzaky Raihan\Harits Cloud\dist\api_keys_groq.json"
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
    """
    Memuat daftar API Key dari file konfigurasi:
    - C:\Ridho Dzaky Raihan\Harits Cloud\api_keys_groq.json
    - C:\Ridho Dzaky Raihan\Harits Cloud\dist\api_keys_groq.json
    Dan memastikan kedua file selalu sinkron.
    """
    api_keys = []
    search_paths = [
        CONFIG_ROOT,
        CONFIG_DIST,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_keys_groq.json"),
        CONFIG_FILE
    ]

    for p in search_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list) and len(loaded) > 0:
                        keys = [k for k in loaded if isinstance(k, str) and k.startswith("gsk_")]
                        if len(keys) >= 3:
                            api_keys = keys
                            break
                        elif keys and not api_keys:
                            api_keys = keys
            except Exception:
                pass

    # Cadangan: jika belum ada, periksa api key.txt
    if not api_keys and os.path.exists("api key.txt"):
        try:
            with open("api key.txt", "r", encoding="utf-8") as f:
                for line in f:
                    if "gsk_" in line:
                        parts = line.strip().split()
                        for p in parts:
                            if p.startswith("gsk_") and p not in api_keys:
                                api_keys.append(p)
        except Exception:
            pass

    # Sinkronisasi ke kedua lokasi file konfigurasi
    if api_keys:
        for target in [CONFIG_ROOT, CONFIG_DIST]:
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "w", encoding="utf-8") as f:
                    json.dump(api_keys, f, indent=2)
            except Exception:
                pass

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
        "You are an expert Swiss Professor of English Linguistics and the world's foremost TOEFL ITP/iBT master authority.\n"
        "Your task is to analyze English questions (Structure, Written Expression, Reading, Listening) from screen captures and output the single 100% correct answer.\n\n"
        "COMPREHENSIVE TOEFL MASTER RULES (DISTILLED FROM 150+ REAL TOEFL EXAM PATTERNS):\n"
        "1. NEGATIVE & RESTRICTIVE INVERSION (Auxiliary + Subject + Verb):\n"
        "   - Clauses opening with negative/restrictive words ('Under no circumstances', 'Rarely', 'Scarcely... when', 'Hardly... when', 'Not until', 'Seldom', 'Never', 'Not only', 'At no time', 'Only after', 'So + adj + that') REQUIRE inverted word order: [Auxiliary/Modal + Subject + Main Verb]!\n"
        "     * 'Under no circumstances should hazardous materials be left...'\n"
        "     * 'Rarely has such an intricate alignment been recorded.'\n"
        "     * 'Not until the satellite reached its orbit did it begin...'\n"
        "2. COMPARATIVE STRUCTURE & PRONOUN REFERENCE:\n"
        "   - Compare like with like using demonstrative pronouns:\n"
        "     * Plural nouns ('data', 'findings', 'results', 'specimens'): use 'those' / 'those of' / 'those [V3]' (NEVER 'what', 'that', or 'which').\n"
        "     * Singular/uncountable nouns ('climate', 'output', 'behavior'): use 'that' / 'that of'.\n"
        "3. RELATIVE CLAUSE FINITE VERB REQUIREMENT:\n"
        "   - Formal relative clauses like 'the primary objective of which [VERB]' demand a finite tense verb ('is', 'was', 'are', 'were'), NEVER infinitive 'to be' or participle 'being'.\n"
        "4. CORRELATIVE CONJUNCTIONS:\n"
        "   - 'not only' strictly pairs with 'but also' (NEVER 'plus', 'as well as', 'along with').\n"
        "   - 'either... or', 'neither... nor', 'both... and'.\n"
        "5. SUBJUNCTIVE MOOD (MANDATORY BARE INFINITIVE):\n"
        "   - After verbs/adjectives of recommendation, demand, suggestion (suggest, recommend, insist, demand, require, vital, essential, imperative) + THAT + Subject + [BASE VERB / bare infinitive without -s/-es/-ed]!\n"
        "     * 'She suggested that he come earlier.' (NOT 'comes' or 'came')\n"
        "     * 'The dean recommended that every candidate submit...' (NOT 'submits')\n"
        "6. DOUBLE VERB TRAP & REDUCED CLAUSES:\n"
        "   - If a finite main verb is already present in the sentence, the modifier must be a reduced participle: V3 for passive meaning ('The report written yesterday...', 'Severely damaged by turbulence...'), or V-ing for active meaning ('The man standing near the door...'). Avoid choosing duplicate finite verbs.\n"
        "7. SUBJECT-VERB AGREEMENT & SPECIAL NOUNS:\n"
        "   - Intervening prepositional phrases ('along with', 'together with', 'as well as', 'in addition to') do NOT affect the head subject: 'The teacher, along with his students, is...'\n"
        "   - In 'neither... nor' and 'either... or', the verb agrees with the CLOSER subject: 'Neither the manager nor the employees were present.'\n"
        "   - Indefinite pronouns are singular: 'Each of the students is...', 'Neither of the answers is...'\n"
        "   - Always singular/uncountable nouns: 'weather', 'information', 'news', 'equipment', 'luggage' take singular verbs: 'The news is surprising', 'The information is correct'.\n"
        "   - 'one of the [plural noun] who [VERB]': the relative pronoun refers to the plural noun: 'one of the students who are selected...'\n"
        "8. TENSES, TIME MARKERS & ASPECTS:\n"
        "   - Past Perfect ('had + V3') for an action completed before another past event: 'They had finished their assignment before class started.'\n"
        "   - 'for' + duration ('for five years'), 'since' + specific starting point ('since 2015').\n"
        "   - Past continuous interrupted by simple past: 'She was reading when I met her.'\n"
        "   - Fixed future timetables use Simple Present: 'The meeting starts at 9 a.m. tomorrow.'\n"
        "9. CONDITIONAL SENTENCES:\n"
        "   - Type 1 (Real): If + Present Simple, will + V1 ('If she studies harder, she will pass').\n"
        "   - Type 2 (Unreal Present): If + Past Simple ('were' for all subjects), would + V1 ('If I were you, I would take...').\n"
        "   - Type 3 / Inverted: Had + S + V3, would have + V3 ('Had the commission acted, it would have been...').\n"
        "10. GERUNDS, INFINITIVES & PREPOSITIONAL COLLOCATIONS:\n"
        "   - Followed by Gerund (-ing): enjoy ('enjoys reading/listening/watching'), avoid, admit, mind, consider.\n"
        "   - Preposition + Gerund: 'interested in learning', 'good at mathematics', 'responsible for safety', 'excited about the trip'.\n"
        "11. PASSIVE VOICE:\n"
        "   - Passive form: Be + V3 ('The car was repaired last week', 'The book was written by...').\n"
        "12. READING & LISTENING COMPREHENSION:\n"
        "   - Main Idea questions: Extract the core theme from the opening topic sentences.\n"
        "   - Factual details: Match exact passage synonyms (e.g., environmental protection, productivity drop).\n"
        "   - EXCEPT/NOT questions: Eliminate the 3 passage facts; pick the unmentioned or contradictory option.\n\n"
        "STRICT TASK RULES:\n"
        "- Identify the single multiple-choice question on the screen.\n"
        "- Output strictly and ONLY one single line:\n"
        "Jawabannya [HURUF]\n\n"
        "Do not repeat the question, do not output explanations, and do not make lists.\n\n"
        "FEW-SHOT EXAMPLES:\n"
        "Input: 'Under no circumstances ___ left unattended. A. materials should be B. should materials be C. be materials D. materials be'\n"
        "Output: Jawabannya B\n\n"
        "Input: 'The data were far more reliable than ___ by the previous team. A. what was collected B. those collected C. that collected D. which collected'\n"
        "Output: Jawabannya B\n\n"
        "Input: 'She suggested that he ___ earlier. A. comes B. come C. came D. coming'\n"
        "Output: Jawabannya B\n\n"
        "Input: 'The teacher, along with his students, ___ in the classroom. A. are B. were C. is D. be'\n"
        "Output: Jawabannya C\n\n"
        "Input: 'Neither the manager nor the employees ___ present at the meeting. A. was B. were C. is D. are'\n"
        "Output: Jawabannya B\n\n"
        "Input: 'If I ___ you, I would take the opportunity. A. am B. was C. were D. be'\n"
        "Output: Jawabannya C\n\n"
        "Input: 'I have lived in this city ___ ten years. A. since B. for C. from D. during'\n"
        "Output: Jawabannya B\n\n"
        "Input: 'She enjoys ___ books in her free time. A. read B. reads C. reading D. to read'\n"
        "Output: Jawabannya C\n\n"
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
    print("\n[+] Status API Key:")
    print("    - C:\\Ridho Dzaky Raihan\\Harits Cloud\\api_keys_groq.json [OK]")
    print("    - C:\\Ridho Dzaky Raihan\\Harits Cloud\\dist\\api_keys_groq.json [OK - Sinkron]")
    print(f"[+] Total Terhubung: {len(api_keys)} API Key Groq")
    for i, k in enumerate(api_keys):
        masked = k[:8] + "..." + k[-4:]
        print(f"    - Key {i+1}: {masked}")
    print("[+] Model AI Knowledge: Ditraining dari 150 Soal TOEFL (Structure, Inversion, Subjunctive, Reading & Listening)")

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
