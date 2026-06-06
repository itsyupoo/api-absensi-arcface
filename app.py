from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

app = FastAPI(title="API Absensi Siswa ArcFace")

# ==========================================
# PYDANTIC SCHEMAS (Validasi Data)
# ==========================================

# Skema data untuk simpan absensi
class AbsenRequest(BaseModel):
    nisn: str
    status: str  # Hadir, Alpa, Izin, Sakit

# Schema untuk Geofencing
class GeofencingSchema(BaseModel):
    latitude_sekolah: float
    longitude_sekolah: float
    radius_meter: float

# Schema untuk Sistem Keamanan
class KeamananSchema(BaseModel):
    status_keamanan: str  # misal: "Aktif" atau "Nonaktif"


# ==========================================
# DATABASE CONNECTION (Cloud Railway)
# ==========================================
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


# ==========================================
# ENDPOINTS UTAMA
# ==========================================

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
        cursor.execute("SELECT * FROM dataset_siswa")
        siswa_data = cursor.fetchall()
        return {"status": "sukses", "data": siswa_data}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# 3. Endpoint Simpan Absensi
@app.post("/absen")
def simpan_absen(data: AbsenRequest):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
    
    cursor = conn.cursor()
    try:
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
def get_geofencing():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM komfigurasi_geofencing ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if not result:
            return {"latitude_sekolah": -2.9602, "longitude_sekolah": 104.7554, "radius_meter": 50.0}
        return {
            "latitude_sekolah": result.get("latitude"),
            "longitude_sekolah": result.get("longitude"),
            "radius_meter": result.get("radius")
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/geofencing/update")
def update_geofencing(data: GeofencingSchema):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
        
    cursor = conn.cursor()
    query = """
        INSERT INTO komfigurasi_geofencing (id, latitude, longitude, radius) 
        VALUES (1, %s, %s, %s) 
        ON DUPLICATE KEY UPDATE 
        latitude=%s, longitude=%s, radius=%s
    """
    values = (data.latitude_sekolah, data.longitude_sekolah, data.radius_meter,
              data.latitude_sekolah, data.longitude_sekolah, data.radius_meter)
    try:
        cursor.execute(query, values)
        conn.commit()
        return {"status": "success", "message": "Konfigurasi geofencing berhasil diperbarui di cloud"}
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ==========================================
# ENDPOINT SISTEM KEAMANAN (Dinamis)
# ==========================================

@app.get("/sistem-keamanan")
def get_status_keamanan():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM sistem_keamanan ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if not result:
            return {"status_keamanan": "Aktif"}
        return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/sistem-keamanan/update")
def update_status_keamanan(data: KeamananSchema):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
        
    cursor = conn.cursor()
    query = """
        INSERT INTO sistem_keamanan (id, status_keamanan) 
        VALUES (1, %s) 
        ON DUPLICATE KEY UPDATE status_keamanan=%s
    """
    try:
        cursor.execute(query, (data.status_keamanan, data.status_keamanan))
        conn.commit()
        return {"status": "success", "message": "Status keamanan berhasil diubah di cloud"}
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()