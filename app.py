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
class SistemKeamananSchema(BaseModel):
    anti_mock_gps: str
    emulator_detection: str
    root_check: str


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
        cursor.execute("SELECT * FROM konfigurasi_geofencing ORDER BY id DESC LIMIT 1")
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
        INSERT INTO konfigurasi_geofencing (id, latitude, longitude, radius) 
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

# ==========================================
# ENDPOINT KEAMANAN SISTEM (FIX FULL COLUMNS)
# ==========================================

@app.get("/sistem-keamanan")
def get_sistem_keamanan():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
        
    cursor = conn.cursor(dictionary=True)
    try:
        # Kita ambil data dari baris ID = 2 sesuai database kamu
        cursor.execute("SELECT * FROM sistem_keamanan WHERE id = 2")
        result = cursor.fetchone()
        
        if not result:
            return {
                "anti_mock_gps": "Aktif",
                "emulator_detection": "Nonaktif",
                "root_check": "Nonaktif"
            }
            
        return {
            "anti_mock_gps": result.get("anti_mock_gps", "Aktif"),
            "emulator_detection": result.get("emulator_detection", "Nonaktif"),
            "root_check": result.get("root_check", "Nonaktif")
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/sistem-keamanan/update")
def update_sistem_keamanan(data: SistemKeamananSchema):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
        
    cursor = conn.cursor()
    # 👉 QUERY FIX: Menembak 3 kolom sekaligus dan mengunci ke ID = 2
    query = """
        INSERT INTO sistem_keamanan (id, anti_mock_gps, emulator_detection, root_check) 
        VALUES (2, %s, %s, %s) 
        ON DUPLICATE KEY UPDATE 
        anti_mock_gps = %s, 
        emulator_detection = %s, 
        root_check = %s
    """
    values = (data.anti_mock_gps, data.emulator_detection, data.root_check,
              data.anti_mock_gps, data.emulator_detection, data.root_check)
    try:
        cursor.execute(query, values)
        conn.commit()
        return {"status": "success", "message": "Konfigurasi keamanan berhasil diperbarui di cloud"}
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ==========================================
# ENDPOINT PRESENSI SISWA (FIX STRUCTURE)
# ==========================================

# Schema baru disesuaikan dengan kolom tabel catatan_kehadiran
class PresensiSchema(BaseModel):
    id_siswa: int
    jarak_geo: float
    status_kehadiran: str  # Hadir / Terlambat
    distance: float        # Nilai threshold kemiripan wajah ArcFace

@app.post("/presensi/hadir")
def catat_presensi(data: PresensiSchema):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Gagal terhubung ke database cloud")
        
    cursor = conn.cursor()
    # Query disesuaikan dengan kolom: id_siswa, waktu_absen, jarak_geo, status_kehadiran, distance
    # waktu_absen diisi otomatis oleh server cloud menggunakan NOW() (tanggal + jam seketika)
    query = """
        INSERT INTO catatan_kehadiran (id_siswa, waktu_absen, jarak_geo, status_kehadiran, distance) 
        VALUES (%s, NOW(), %s, %s, %s)
    """
    values = (data.id_siswa, data.jarak_geo, data.status_kehadiran, data.distance)
    try:
        cursor.execute(query, values)
        conn.commit()
        return {"status": "success", "message": "Catatan kehadiran berhasil disimpan di cloud MySQL!"}
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()