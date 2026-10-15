# Harits Cloud - Auto Ketik AI

Aplikasi otomatisasi asisten pengetikan pintar menggunakan AI (**Google Gemini** dan **Groq**) berbasis Python. Program membaca pertanyaan dari clipboard atau input, menghasilkan respons yang ringkas dan padat, serta mengetikkan jawaban secara otomatis ke layar aktif.

---

## 🌟 Fitur Utama

- **Integrasi Multi-AI**:
  - **Gemini**: Menggunakan model Google Gemini dengan gaya bahasa natural mahasiswa.
  - **Groq**: Respons ultra-cepat berbasis Llama/Mixtral di cloud Groq.
- **Auto-Ketik Otomatis**: Mengetikkan jawaban secara presisi ke aplikasi target menggunakan simulasi keyboard (`pyautogui` & `pyperclip`).
- **Rotasi API Key**: Mendukung hingga 3 API Key secara bergantian untuk menghindari limit kuota.
- **Penyimpanan Kredensial Lokal**: API key tersimpan secara lokal dan otomatis dipanggil tanpa perlu input ulang setiap sesi.

---

## 📁 Struktur Direktori

```text
├── auto_ketik_gemini.py       # Script auto-ketik dengan Gemini AI
├── auto_ketik_groq.py         # Script auto-ketik dengan Groq AI
├── auto_ketik_gemini.spec     # Konfigurasi build PyInstaller (Gemini)
├── auto_ketik_groq.spec       # Konfigurasi build PyInstaller (Groq)
├── api_keys_config.example.json # Template konfigurasi API Key Gemini
├── api_keys_groq.example.json   # Template konfigurasi API Key Groq
├── docs api gemini.md         # Dokumentasi referensi API Gemini
├── docs api groq.md           # Dokumentasi referensi API Groq
├── requirements.txt           # Dependensi Python
└── README.md                  # Dokumentasi project
```

---

## 🚀 Panduan Instalasi & Penggunaan

### 1. Prasyarat
Pastikan Anda telah menginstal **Python 3.10+**.

### 2. Instalasi Dependensi
Jalankan perintah berikut di terminal:
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi API Key
Salin file template contoh dan ubah dengan API Key Anda sendiri:

- **Untuk Gemini**:
  ```bash
  cp api_keys_config.example.json api_keys_config.json
  ```
  Dapatkan API key dari [Google AI Studio](https://aistudio.google.com/api-keys).

- **Untuk Groq**:
  ```bash
  cp api_keys_groq.example.json api_keys_groq.json
  ```
  Dapatkan API key gratis dari [Groq Console](https://console.groq.com/keys).

*(Catatan: Anda juga bisa langsung menjalankan script, dan program akan meminta input API key pada eksekusi pertama).*

### 4. Menjalankan Aplikasi
- **Menggunakan Gemini**:
  ```bash
  python auto_ketik_gemini.py
  ```
- **Menggunakan Groq**:
  ```bash
  python auto_ketik_groq.py
  ```

---

## ⚠️ Keamanan
File kredensial seperti `api_keys_config.json`, `api_keys_groq.json`, serta file catatan API Key diabaikan secara default melalui `.gitignore` untuk mencegah kebocoran kunci rahasia ke publik.
