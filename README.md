# Instagram-Like-Bot 

Bot sederhana yang me-like postingan Instagram berdasarkan hashtag, memakai **Selenium 4 + Firefox**.
Ditulis ulang dari proyek asli [kevinam99/Instagram-Like-Bot](https://github.com/kevinam99/Instagram-Like-Bot) (MIT) agar jalan di Kali Linux terbaru.

> ⚠️ **Disclaimer:** Otomasi like melanggar Terms of Use Instagram dan dapat menyebabkan akun dibatasi atau diblokir.
> Proyek ini untuk belajar otomasi web. Gunakan akun uji, dengan risiko sendiri.

## Perubahan dari versi lama
- Selenium 4 (`By.*`, `WebDriverWait`), geckodriver otomatis (Selenium Manager), tanpa `webdriverdownloader`.
- Selector berbasis `aria-label`, bukan class CSS acak yang cepat usang.
- GUI berjalan di thread terpisah (tidak membeku), ada tombol Stop dan log langsung.
- Mode CLI (`--cli`), password tidak pernah dicetak.
- Jeda acak, batas like per sesi, deteksi "Action Blocked" lalu berhenti.
- Dihapus: Kivy/buildozer/Android (tidak berfungsi).

## Instalasi (Kali Linux)
```bash
git clone https://github.com/spyschools/Instagram-Like-Bot.git
cd Instagram-Like-Bot
./install.sh
```

## Pemakaian
```bash
source venv/bin/activate

# GUI
python3 main.py

# Terminal
python3 main.py --cli -u akun_uji -t python,linux --max-likes 20
python3 main.py --cli -u akun_uji -t python --headless   # tanpa jendela```

# NONAKTIFKAN
deactivate

Password dibaca dari env `IG_PASSWORD` atau diminta secara tersembunyi.
Jika Instagram meminta 2FA/verifikasi, jalankan tanpa `--headless` dan selesaikan manual di Firefox.

## Troubleshooting
- **`externally-managed-environment`**: jangan `pip install` global, gunakan venv (sudah ditangani `install.sh`).
- **Tombol like tidak ditemukan**: UI Instagram berubah, perbarui `LIKE_XPATH` di `scraper.py`.
- **GUI tidak muncul** (SSH/headless): pakai mode `--cli`.
- **Action Blocked**: bot berhenti otomatis; tunggu beberapa jam dan turunkan `--max-likes`.

## Lisensi
MIT, hak cipta asli Kevin A Mathew dipertahankan.
