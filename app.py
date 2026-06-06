from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
from pydantic import BaseModel

# Schema untuk Geofencing
class GeofencingSchema(BaseModel):
    latitude_sekolah: float
    longitude_sekolah: float
    radius_meter: float

# Schema untuk Sistem Keamanan
class KeamananSchema(BaseModel):
    status_keamanan: str  # misal: "Aktif" atau "Nonaktif"

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

    # ==========================================
# ENDPOINT GEOFENCING (Dinamis)
# ==========================================

@app.get("/geofencing")
def get_geofencing(db = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    # Mengambil konfigurasi geofencing terbaru dari tabel
    cursor.execute("SELECT * FROM komfigurasi_geofencing ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    if not result:
        # Jika tabel masih kosong, ini nilai default (koordinat Palembang / SMA Sjakhyakirti)
        return {"latitude_sekolah": -2.9602, "longitude_sekolah": 104.7554, "radius_meter": 50.0}
    return result

@app.post("/geofencing/update")
def update_geofencing(data: GeofencingSchema, db = Depends(get_db)):
    cursor = db.cursor()
    # Query untuk memperbarui data di ID=1 secara dinamis
    query = """
        INSERT INTO komfigurasi_geofencing (id, latitude_sekolah, longitude_sekolah, radius_meter) 
        VALUES (1, %s, %s, %s) 
        ON DUPLICATE KEY UPDATE 
        latitude_sekolah=%s, longitude_sekolah=%s, radius_meter=%s
    """
    values = (data.latitude_sekolah, data.longitude_sekolah, data.radius_meter,
              data.latitude_sekolah, data.longitude_sekolah, data.radius_meter)
    try:
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        return {"status": "success", "message": "Konfigurasi geofencing berhasil diperbarui di cloud"}
    except Exception as e:
        db.rollback()
        cursor.close()
        return {"status": "error", "message": str(e)}


# ==========================================
# ENDPOINT SISTEM KEAMANAN (Dinamis)
# ==========================================

@app.get("/sistem-keamanan")
def get_status_keamanan(db = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sistem_keamanan ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    if not result:
        return {"status_keamanan": "Aktif"}
    return result

@app.post("/sistem-keamanan/update")
def update_status_keamanan(data: KeamananSchema, db = Depends(get_db)):
    cursor = db.cursor()
    query = """
        INSERT INTO sistem_keamanan (id, status_keamanan) 
        VALUES (1, %s) 
        ON DUPLICATE KEY UPDATE status_keamanan=%s
    """
    try:
        cursor.execute(query, (data.status_keamanan, data.status_keamanan))
        db.commit()
        cursor.close()
        return {"status": "success", "message": "Status keamanan berhasil diubah di cloud"}
    except Exception as e:
        db.rollback()
        cursor.close()
        return {"status": "error", "message": str(e)}    