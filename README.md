# 📱 Presensi SMA Sjakhyakirti — Flet App

Aplikasi presensi berbasis mobile menggunakan **Python + Flet**.

---

## 📁 Struktur Project

```
presensi_app/
├── main.py                        ← Entry point utama
├── requirements.txt
├── components/
│   └── ui.py                      ← Komponen & warna reusable
└── views/
    ├── login.py                   ← Halaman login (siswa & admin)
    ├── siswa/
    │   ├── dashboard.py           ← Dashboard siswa
    │   ├── presensi.py            ← Kamera + verifikasi ArcFace
    │   ├── riwayat.py             ← Riwayat kehadiran
    │   └── profil.py              ← Profil & info orang tua
    └── admin/
        ├── dashboard.py           ← Statistik + grafik + WA status
        ├── monitoring.py          ← Log real-time + filter
        ├── data_siswa.py          ← CRUD siswa + enrollment ArcFace
        └── settings.py            ← Geofencing + Sheets + WA template
```

---

## ⚙️ Setup di VS Code

### 1. Buat Virtual Environment
```bash
python -m venv venv
```

### 2. Aktifkan Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```
**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependensi
```bash
pip install -r requirements.txt
```

### 4. Jalankan aplikasi (mode desktop/browser)
```bash
flet run main.py
```

### 5. Jalankan mode web (bisa diakses di browser)
```bash
flet run --web main.py
```

### 6. Jalankan sebagai tampilan mobile (portrait 390×844)
```bash
flet run --web --port 8080 main.py
```
Kemudian buka browser → Developer Tools → Toggle device toolbar → pilih iPhone 14.

---

## 🔐 Akun Demo

| Role  | NIS/NIP | Password  |
|-------|---------|-----------|
| Siswa | 12345   | password  |
| Admin | 99001   | password  |

---

## 📱 Build ke Android (APK)

### Prasyarat
- Sudah install **Android Studio** + Android SDK
- Sudah install **Flutter SDK** (dibutuhkan Flet untuk build)

### Langkah build APK
```bash
# Install flet-cli jika belum ada
pip install flet

# Build APK
flet build apk
```

APK akan tersedia di folder `build/apk/`.

---

## 🎨 Kustomisasi

### Mengubah warna tema
Edit konstanta `C` di `components/ui.py`:
```python
C = {
    "blue":  "#4F8EF7",   # warna utama
    "green": "#22D3A0",   # sukses / hadir
    "red":   "#F75F5F",   # error / alfa
    ...
}
```

### Menghubungkan ke backend nyata
Ganti data dummy di masing-masing view dengan API call ke backend Railway/FastAPI kamu.
Contoh di `views/login.py`:
```python
import httpx

async def do_login(self, e):
    resp = await httpx.AsyncClient().post(
        "https://your-api.railway.app/auth/login",
        json={"username": username, "password": password}
    )
    data = resp.json()
    ...
```

---

## 🧩 Ekstensi VS Code yang Disarankan

- **Python** (Microsoft)
- **Pylance**
- **Flutter** (jika ingin build ke APK)

---

## 📝 Catatan

- Kamera real-time belum diimplementasikan (placeholder) — integrasikan dengan `camera` plugin Flet saat tersedia, atau gunakan `opencv-python` untuk desktop.
- GPS / geofencing adalah simulasi — hubungkan ke `geolocator` saat deploy ke Android.
- WhatsApp gateway menggunakan Fonnte API — masukkan API key di tab Settings admin.
