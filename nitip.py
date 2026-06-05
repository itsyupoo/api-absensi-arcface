import mysql.connector
import json
import numpy as np
from datetime import datetime

def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="db_presensi_siswa" 
        )
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# --- TABEL 1: dataset_siswa (Untuk Registrasi) ---
def simpan_siswa(nis, nama, kelas, wa, face_embedding, jk):
    db = None
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        if isinstance(face_embedding, np.ndarray):
            face_embedding = face_embedding.tolist()
        embedding_json = json.dumps(face_embedding)

        sql = "INSERT INTO dataset_siswa (nis, nama, jenis_kelamin, kelas, wa_ortu, face_embedding, password, role) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        password_default = "sjakhyakirti2026"
        role_default = "siswa"
        val = (nis, nama, jk, kelas, wa, embedding_json, password_default, role_default)
        cursor.execute(sql, val)
        db.commit() 
        return True
        
    except Exception as e:
        print(f">>> ERROR DATABASE: {e}")
        return False
        
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def ambil_semua_wajah():
    conn = get_db_connection()
    daftar_wajah = []
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT id_siswa, nama, nis, kelas, wa_ortu, jenis_kelamin, face_embedding FROM dataset_siswa WHERE role = 'siswa' AND face_embedding IS NOT NULL"
            cursor.execute(query)
            
            for (id_siswa, nama, nis, kelas, wa, jk, face_emb) in cursor:
                try:
                    if face_emb:
                        embedding = np.array(json.loads(face_emb), dtype=np.float32)

                        if embedding.shape == (512,):
                            daftar_wajah.append({
                            "id_siswa": id_siswa, 
                            "nama": nama,          
                            "nis": nis,
                            "kelas": kelas,        
                            "wa_ortu": wa, 
                            "jenis_kelamin": jk, 
                            "embedding": embedding
                        })
                    else:
                            print(f">>> WARN: Data {nama} diabaikan karena ukuran bukan 512.")
                except Exception as e_row:
                    print(f">>> WARN: Gagal memproses embedding siswa {nama}: {e_row}")
                    continue

        except Exception as e:
            print(f">>> ERROR saat ambil data: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return daftar_wajah

# --- TABEL 2: catatan_kehadiran (Untuk Absensi) ---
def catat_kehadiran(id_siswa, jarak_geo):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO catatan_kehadiran (id_siswa, jarak_geo) VALUES (%s, %s)"
        cursor.execute(sql, (id_siswa, jarak_geo))
        conn.commit()
        conn.close()

# --- TABEL 3: konfigurasi_geofencing (Untuk Pengaturan Lokasi Sekolah) ---
def simpan_pengaturan_geofencing(lat, lng, radius):
    """Menyimpan atau memperbarui lokasi pusat sekolah dan radiusnya"""
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM konfigurasi_geofencing")
            
            sql = "INSERT INTO konfigurasi_geofencing (latitude, longitude, radius) VALUES (%s, %s, %s)"
            val = (lat, lng, radius)
            
            cursor.execute(sql, val)
            db.commit()
            return True
        except Exception as e:
            print(f">>> ERROR SIMPAN GEOFENCING: {e}")
            return False
        finally:
            cursor.close()
            db.close()
    return False

def proses_login(username, password_input):
    """
    Memeriksa kredensial login dari tabel dataset_siswa.
    Username bisa berisi NIS (untuk siswa) atau NIP (untuk admin).
    """
    conn = get_db_connection()
    user_data = None
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM dataset_siswa WHERE nis = %s AND password = %s"
            cursor.execute(query, (username, password_input))
            
            user_data = cursor.fetchone()
            
        except Exception as e:
            print(f">>> ERROR LOGIN: {e}")
        finally:
            conn.close()
            
    return user_data 

def ambil_pengaturan_geofencing():
    """Mengambil data latitude, longitude, dan radius untuk keperluan absensi"""
    db = get_db_connection()
    data = None
    if db:
        try:
            cursor = db.cursor(dictionary=True) 
            cursor.execute("SELECT latitude, longitude, radius FROM konfigurasi_geofencing LIMIT 1")
            data = cursor.fetchone()
        except Exception as e:
            print(f">>> ERROR AMBIL GEOFENCING: {e}")
        finally:
            cursor.close()
            db.close()
    
    if not data:
        return {"latitude": "-2.994583", "longitude": "104.756111", "radius": "100"}
        
    return data

def simpan_keamanan_sistem(anti_mock, emulator, root):
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM sistem_keamanan")
            
            sql = "INSERT INTO sistem_keamanan (anti_mock_gps, emulator_detection, root_check) VALUES (%s, %s, %s)"
            val = (anti_mock, emulator, root)
            
            cursor.execute(sql, val)
            db.commit()
            return True
        except Exception as e:
            print(f">>> ERROR DATABASE KEAMANAN: {e}")
            return False
        finally:
            cursor.close()
            db.close()
    return False

def ambil_statistik_dashboard():
    """Mengambil total siswa dan status kehadiran hari ini"""
    conn = get_db_connection()
    stats = {"total": 0, "hadir": 0, "terlambat": 0, "belum": 0}
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM dataset_siswa")
            stats['total'] = cursor.fetchone()['total']
            query_absen = """
                SELECT 
                    COUNT(CASE WHEN TIME(waktu_absen) <= '07:15:00' THEN 1 END) as hadir_tepat,
                    COUNT(CASE WHEN TIME(waktu_absen) > '07:15:00' THEN 1 END) as terlambat
                FROM catatan_kehadiran 
                WHERE DATE(waktu_absen) = CURDATE()
            """
            cursor.execute(query_absen)
            res = cursor.fetchone()
            stats['hadir'] = res['hadir_tepat'] or 0
            stats['terlambat'] = res['terlambat'] or 0
            
            stats['belum'] = stats['total'] - (stats['hadir'] + stats['terlambat'])
            
        except Exception as e:
            print(f">>> ERROR STATS DASHBOARD: {e}")
        finally:
            conn.close()
    return stats

def ambil_presensi_terbaru(limit=5):
    """Mengambil daftar siswa terakhir yang melakukan presensi hari ini"""
    conn = get_db_connection()
    hasil = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT s.nama, s.kelas, c.waktu_absen,
                       CASE WHEN TIME(c.waktu_absen) <= '07:15:00' THEN 'Hadir' ELSE 'Terlambat' END as status
                FROM catatan_kehadiran c
                JOIN dataset_siswa s ON c.id_siswa = s.id_siswa
                WHERE DATE(c.waktu_absen) = CURDATE()
                ORDER BY c.waktu_absen DESC 
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            hasil = cursor.fetchall()
        finally:
            conn.close()
    return hasil

def ambil_rekap_7_hari():
    """Mengambil jumlah kehadiran hanya pada hari-hari yang ada aktivitas absen"""
    conn = get_db_connection()
    rekap_data = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT DATE(waktu_absen) as tanggal, COUNT(*) as jumlah
                FROM catatan_kehadiran
                GROUP BY DATE(waktu_absen)
                ORDER BY tanggal DESC
                LIMIT 7
            """
            cursor.execute(query)
            results = cursor.fetchall()
            
            results.reverse()
            
            nama_hari = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
            for row in results:
                tgl = row['tanggal']
                label = nama_hari[tgl.weekday()]
                rekap_data.append((label, row['jumlah']))
                
        finally:
            conn.close()
            
    return rekap_data

def cari_riwayat_siswa(nama_query=None):
    """Mencari riwayat kehadiran berdasarkan nama siswa"""
    conn = get_db_connection()
    hasil = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            if nama_query:
                query = """
                    SELECT s.nama, s.kelas, c.waktu_absen,
                           CASE WHEN TIME(c.waktu_absen) <= '07:15:00' THEN 'Hadir' ELSE 'Terlambat' END as status
                    FROM catatan_kehadiran c
                    JOIN dataset_siswa s ON c.id_siswa = s.id_siswa
                    WHERE s.nama LIKE %s
                    ORDER BY c.waktu_absen DESC
                """
                cursor.execute(query, (f"%{nama_query}%",))
            else:
                query = """
                    SELECT s.nama, s.kelas, c.waktu_absen,
                           CASE WHEN TIME(c.waktu_absen) <= '07:15:00' THEN 'Hadir' ELSE 'Terlambat' END as status
                    FROM catatan_kehadiran c
                    JOIN dataset_siswa s ON c.id_siswa = s.id_siswa
                    WHERE DATE(c.waktu_absen) = CURDATE()
                    ORDER BY c.waktu_absen DESC
                """
                cursor.execute(query)
                
            hasil = cursor.fetchall()
        finally:
            conn.close()
    return hasil

def ambil_statistik_siswa(id_siswa):
    db = get_db_connection()
    stats = {"hadir": 0, "terlambat": 0, "persen": "0%"}
    if db:
        try:
            cursor = db.cursor()
        # Hitung Hadir
            cursor.execute("SELECT COUNT(*) FROM catatan_kehadiran WHERE id_siswa = %s AND status_kehadiran = 'Hadir'", (id_siswa,))
            stats["hadir"] = cursor.fetchone()[0] or 0
        
        # Hitung Terlambat
            cursor.execute("SELECT COUNT(*) FROM catatan_kehadiran WHERE id_siswa = %s AND status_kehadiran = 'Terlambat'", (id_siswa,))
            stats["terlambat"] = cursor.fetchone()[0] or 0
        
        # Hitung Persentase (Asumsi 1 semester 100 hari efektif)
            total = stats["hadir"] + stats["terlambat"]
            if total > 0:
                persen_hitung = (total / 100) * 100
                stats["persen"] = f"{int(persen_hitung)}%"
            else:
                stats["persen"] = "0%"
        except Exception as e:
            print(f"Error statistik: {e}")
        finally:
            db.close()
    return stats

def cek_presensi_hari_ini(id_siswa):
    import datetime
    db = get_db_connection()
    status = False
    if db:
        try:
            cursor = db.cursor()
            hari_ini = datetime.datetime.now().strftime("%Y-%m-%d")
            query = "SELECT id_presensi FROM catatan_kehadiran WHERE id_siswa = %s AND DATE(waktu_absen) = %s"
            cursor.execute(query, (id_siswa, hari_ini))
            if cursor.fetchone():
                status = True
        finally:
            db.close()
    return status

def ambil_notifikasi_siswa(id_siswa):
    db = get_db_connection()
    notif_list = []
    if db:
        try:
            cursor = db.cursor(dictionary=True)
            query = """
                SELECT status_kehadiran, waktu_absen FROM catatan_kehadiran WHERE id_siswa = %s ORDER BY waktu_absen DESC LIMIT 3
            """
            cursor.execute(query, (id_siswa,))
            results = cursor.fetchall()
            
            for row in results:
                waktu = row['waktu_absen'].strftime("%d %b, %H:%M")
                icon = "✅" if row['status_kehadiran'] == 'Hadir' else "⚠️"
                pesan = f"Presensi {row['status_kehadiran']} tercatat pada {waktu}"
                notif_list.append((icon, pesan, False))
        finally:
            db.close()
            
    if not notif_list:
        notif_list = [("ℹ️", "Belum ada aktivitas presensi.", False)]
        
    return notif_list

def simpan_presensi_face(id_siswa, distance):
    """Menyimpan hasil verifikasi wajah ke tabel catatan_kehadiran"""
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor()
            sekarang = datetime.now()
            jam_sekarang = sekarang.time()
            
            # Logika status berdasarkan jam operasional sekolahmu
            status_kehadiran = "Hadir" if jam_sekarang <= datetime.strptime("07:15:00", "%H:%M:%S").time() else "Terlambat"
            sql = """
                INSERT INTO catatan_kehadiran (id_siswa, status_kehadiran, distance, waktu_absen) 
                VALUES (%s, %s, %s, %s)
            """
            val = (id_siswa, status_kehadiran, float(distance), sekarang)
            
            cursor.execute(sql, val)
            db.commit()
            print(f">>> DB: Presensi {id_siswa} berhasil disimpan sebagai {status_kehadiran}")
            return True
        except Exception as e:
            print(f">>> DB ERROR: Gagal simpan presensi: {e}")
            return False
        finally:
            cursor.close()
            db.close()
    return False