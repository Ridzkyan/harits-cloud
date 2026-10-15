import time
import pyperclip
import pyautogui
from google import genai
import sys
import os
import json

CONFIG_FILE = "api_keys_config.json"

def main():
    print("="*50)
    print("🚀 AUTO KETIK JAWABAN GEMINI (MAHASISWA STYLE) 🚀")
    print("="*50)
    
    api_keys = []
    
    # Coba load API keys dari file
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                api_keys = json.load(f)
        except:
            pass

    if api_keys:
        print(f"\n[+] Otomatis menggunakan {len(api_keys)} API Key yang tersimpan sebelumnya!")

    if not api_keys:
        print("\n[+] Silakan masukkan 3 API Key Gemini Anda.")
        print("    (Biarkan kosong jika kurang dari 3. Dapatkan dari: https://aistudio.google.com/api-keys)\n")
        api_key_1 = input("API Key 1: ").strip()
        api_key_2 = input("API Key 2: ").strip()
        api_key_3 = input("API Key 3: ").strip()

        api_keys = [k for k in [api_key_1, api_key_2, api_key_3] if k]

        if not api_keys:
            print("\n[!] Anda harus memasukkan setidaknya 1 API Key!")
            sys.exit()
            
        # Simpan API keys ke file untuk penggunaan berikutnya
        with open(CONFIG_FILE, 'w') as f:
            json.dump(api_keys, f)
        print("\n[+] API Key berhasil disimpan secara permanen!")

    print("\n[+] Sistem siap digunakan!\n")

    def get_gemini_response(prompt, keys):
        # Prompt sistem yang sangat ketat agar AI menjawab cepat, hemat token, dan akurat
        sys_prompt = (
            "Kamu adalah mahasiswa tingkat akhir yang sangat cerdas. Jawab soal berikut dengan FAKTA YANG PASTI BENAR, JUJUR, AKURAT, dan PRESISI. "
            "WAKTU SANGAT TERBATAS. Jawab LANGSUNG TO THE POINT ke inti jawaban. "
            "Gaya bahasa mahasiswa natural. "
            "WAJIB PENDEK DAN PADAT: Minimal 20 kata, tapi MAKSIMAL 40 KATA atau 2-3 kalimat saja! "
            "Dilarang keras memberikan penjelasan bertele-tele atau kata sambutan."
        )
        
        full_prompt = f"{sys_prompt}\n\nPertanyaan: {prompt}"

        # Load balancing / Fallback
        for idx, key in enumerate(keys):
            try:
                client = genai.Client(api_key=key)
                
                # Meminta jawaban ke AI menggunakan model terbaru
                interaction = client.interactions.create(
                    model="gemini-3.8-flash",
                    input=full_prompt
                )
                
                # Jika berhasil, kembalikan teks jawaban dan nomor key yang berhasil
                return interaction.output_text, idx + 1
            except Exception as e:
                error_msg = str(e).lower()
                print(f"  [!] API Key {idx + 1} Error/Limit: {e}")
                print(f"  [*] Mengalihkan ke API Key berikutnya...")
        
        return None, -1

    while True:
        try:
            print("-" * 50)
            input("[ENTER] Jika soal sudah di-copy (Ctrl+C), tekan ENTER di sini...")
            
            # 1. Ambil teks dari clipboard
            soal = pyperclip.paste().strip()
            
            if not soal:
                print("[-] Clipboard Anda kosong. Silakan copy teks soal terlebih dahulu!")
                continue
                
            print(f"\n[*] Membaca soal: {soal[:50]}...")
            print("[*] Sedang berpikir mencari jawaban...")
            
            # 2. Dapatkan jawaban dari Gemini
            jawaban, key_used = get_gemini_response(soal, api_keys)
            
            if jawaban:
                print(f"[+] Jawaban didapat (Menggunakan API Key {key_used}).")
                
                # 3. Hitung mundur agar user punya waktu untuk memindahkan kursor ke browser
                print("\n[!!!] BURUAN KLIK KOLOM INPUT DI BROWSER ANDA! [!!!]")
                for i in range(3, 0, -1):
                    print(f"[*] Mengetik otomatis dalam {i} detik...")
                    time.sleep(1)
                
                print("[*] Mulai mengetik dengan kecepatan kilat...")
                
                # 4. Ketik otomatis
                # interval dipercepat menjadi 0.002 detik (sangat cepat)
                pyautogui.write(jawaban, interval=0.002)
                
                print("[+] Selesai mengetik!\n")
            else:
                print("[-] Gagal mendapatkan jawaban. Semua API Key limit/error.\n")
                
        except KeyboardInterrupt:
            print("\n[+] Program dihentikan.")
            break
        except Exception as e:
            print(f"\n[!] Terjadi kesalahan: {e}")

if __name__ == "__main__":
    main()
