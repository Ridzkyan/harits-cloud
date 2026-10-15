import time
import pyperclip
import pyautogui
from groq import Groq
import sys
import os
import json

CONFIG_FILE = "api_keys_groq.json"

def main():
    print("="*50)
    print("🚀 AUTO KETIK JAWABAN GROQ (SANGAT CEPAT) 🚀")
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
        print(f"\n[+] Otomatis menggunakan {len(api_keys)} API Key Groq yang tersimpan sebelumnya!")

    if not api_keys:
        print("\n[+] Silakan masukkan 3 API Key GROQ Anda.")
        print("    (Dapatkan gratis dari: https://console.groq.com/keys)\n")
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

    def get_groq_response(prompt, keys):
        sys_prompt = (
            "Kamu adalah mahasiswa cerdas. Teks dari user adalah hasil copy-paste dari e-learning (mengandung menu, tombol, dsb). "
            "TUGASMU: 1. Abaikan menu/tombol yang tidak penting. 2. Pahami materi utamanya dan cari tahu apa pertanyaannya (misal disuruh membuat ringkasan materi). "
            "3. Berikan jawaban/ringkasan yang SANGAT SESUAI dengan konteks materi tersebut menggunakan FAKTA YANG BENAR. "
            "4. Gunakan BAHASA INDONESIA dengan gaya bahasa mahasiswa yang natural, cerdas, dan tidak kaku. "
            "5. PANJANG JAWABAN: Buatkan kurang lebih 50 KATA (sekitar 4-6 kalimat yang informatif dan padat). "
            "6. LANGSUNG TO THE POINT tanpa intro/basa-basi apapun!"
        )

        # Load balancing / Fallback
        for idx, key in enumerate(keys):
            try:
                client = Groq(api_key=key)
                
                # Meminta jawaban ke AI menggunakan model tercepat (Llama-3.1-8B-Instant)
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": sys_prompt,
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model="openai/gpt-oss-20b",
                )
                
                return chat_completion.choices[0].message.content.strip(), idx + 1
            except Exception as e:
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
            print("[*] Sedang berpikir secepat kilat (Groq)...")
            
            # 2. Dapatkan jawaban dari Groq
            jawaban, key_used = get_groq_response(soal, api_keys)
            
            if jawaban:
                print(f"[+] Jawaban didapat (Menggunakan API Key {key_used}).")
                
                # 3. Hitung mundur
                print("\n[!!!] BURUAN KLIK KOLOM INPUT DI BROWSER ANDA! [!!!]")
                for i in range(3, 0, -1):
                    print(f"[*] Mengetik otomatis dalam {i} detik...")
                    time.sleep(1)
                
                print("[*] Mulai mengetik dengan kecepatan kilat...")
                
                # 4. Ketik otomatis
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
