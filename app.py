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
@app.get("/siswa")
def get_all_siswa():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM dataset_siswa") # Sesuaikan nama tabel siswa di databasemu
        siswa_data = cursor.fetchall()
        return {"status": "sukses", "data": siswa_data}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# Skema data untuk simpan absensi
class AbsenRequest(BaseModel):
    nisn: str
    status: str  # Hadir, Alpa, Izin, Sakit

# 3. Endpoint Simpan Absensi & Trigger WhatsApp Orang Tua
@app.post("/absen")
def simpan_absen(data: AbsenRequest):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
    
    cursor = conn.cursor()
    try:
        # Contoh query simpan absen (Sesuaikan dengan struktur tabel absensimu)
        query = "INSERT INTO catatan_kehadiran (nisn, status_kehadiran, waktu_absen) VALUES (%s, %s, NOW())"
        cursor.execute(query, (data.nisn, data.status))
        conn.commit()
        
        # TODO: Di sini nanti kita selipkan kodingan kirim WhatsApp via Fonnte
        
        return {"status": "sukses", "pesan": f"Absensi NISN {data.nisn} berhasil dicatat!"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()