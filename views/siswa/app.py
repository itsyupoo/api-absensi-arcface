from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

app = FastAPI(title="API Absensi Siswa ArcFace")

# Fungsi untuk koneksi ke Database Cloud Railway
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="acela.proxy.rlwy.net",
            user="root",
            password="WvjsVeVkcyvgqYyLIEiHBTRgLFkzWAzK",
            database="railway",
            port=33414
        )
        return connection
    except Error as e:
        print(f"Error database: {e}")
        return None

# 1. Endpoint Test: Untuk memastikan API berjalan
@app.get("/")
def home():
    return {"status": "sukses", "pesan": "API Absensi Cloud Railway Aktif!"}

# 2. Endpoint Ambil Data Siswa (Dipakai aplikasi Flet saat login/buka app)
# 2. Endpoint Ambil Data Siswa (Sekarang menembak ke tabel dataset_siswa)
@app.get("/siswa")
def get_all_siswa():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
    
    cursor = conn.cursor(dictionary=True)
    try:
        # --- UBAH DI SINI: ganti 'siswa' menjadi 'dataset_siswa' ---
        cursor.execute("SELECT * FROM dataset_siswa") 
        siswa_data = cursor.fetchall()
        return {"status": "sukses", "data": siswa_data}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error MySQL Spesifik: {str(e)}")
    finally:
        cursor.close()
        conn.close()


# 3. Endpoint Simpan Absensi (Sekarang menembak ke tabel catatan_kehadiran)
@app.post("/absen")
def simpan_absen(data: AbsenRequest):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
    
    cursor = conn.cursor()
    try:
        # --- UBAH DI SINI: ganti 'absensi' menjadi 'catatan_kehadiran' ---
        # Catatan: Sesuaikan nama kolom (nisn, status) dengan kolom asli di tabel catatan_kehadiranmu
        query = "INSERT INTO catatan_kehadiran (nisn, status, waktu) VALUES (%s, %s, NOW())"
        cursor.execute(query, (data.nisn, data.status))
        conn.commit()
        
        return {"status": "sukses", "pesan": f"Absensi NISN {data.nisn} berhasil dicatat!"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()