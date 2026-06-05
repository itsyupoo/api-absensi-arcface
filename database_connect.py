import mysql.connector
import json
import numpy as np
from datetime import datetime
import requests


def get_db_connection():
    try:
        return mysql.connector.connect(
            host="acela.proxy.rlwy.net",
            user="root",
            password="WvjsVeVkcyvgqYyLIEiHBTRgLFkzWAzK",
            database="railway", 
            port=33414
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
def simpan_presensi(id_siswa, distance, jarak_geo):
    """
    Mengisi SATU BARIS PENUH tabel catatan_kehadiran dengan data wajah dan geofencing
    """
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor()
            sekarang = datetime.now()
            jam_sekarang = sekarang.time()
            
            # Batas jam operasional sekolah SMA Sjakhyakirti Palembang (07:15)
            batas_waktu = datetime.strptime("07:15:00", "%H:%M:%S").time()
            status_kehadiran = "Hadir" if jam_sekarang <= batas_waktu else "Terlambat"
            
            # Query diperbarui untuk menangkap skor ArcFace (distance) DAN jarak koordinat (jarak_geo)
            sql = """
                INSERT INTO catatan_kehadiran (id_siswa, status_kehadiran, distance, jarak_geo, waktu_absen) 
                VALUES (%s, %s, %s, %s, %s)
            """
            val = (id_siswa, status_kehadiran, float(distance), float(jarak_geo), sekarang)
            
            cursor.execute(sql, val)
            db.commit()
            print(f">>> DB: Presensi ID {id_siswa} SUKSES. Status: {status_kehadiran}, Jarak: {jarak_geo:.2f}m")
            return True
        except Exception as e:
            print(f">>> DB ERROR: Gagal simpan presensi full: {e}")
            return False
        finally:
            cursor.close()
            db.close()
    return False

# --- TABEL 3: konfigurasi_geofencing (Untuk Pengaturan Lokasi Sekolah) ---
def simpan_pengaturan_geofencing(lat, lng, radius):
    """Menyimpan atau memperbarui lokasi pusat sekolah, dan radiusnya"""
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
            print(f">>> ERROR SIMPAN CONFIG: {e}")
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
    db = get_db_connection()
    data = None
    if db:
        try:
            cursor = db.cursor(dictionary=True) 
            # Pastikan kolom template_wa dimasukkan ke dalam SELECT
            cursor.execute("SELECT latitude, longitude, radius, template_wa FROM konfigurasi_geofencing LIMIT 1")
            data = cursor.fetchone()
        except Exception as e:
            print(f">>> ERROR AMBIL GEOFENCING: {e}")
        finally:
            cursor.close()
            db.close()
    
    # KUNCI UTAMA: Jika tabel kosong, pastikan key "template_wa" juga ada di fallback ini!
    if not data:
        return {
            "latitude": "-2.994583", 
            "longitude": "104.756111", 
            "radius": "100",
            "template_wa": "Presensi {nama} Kelas {kelas} tercatat {status} pada {jam}."
        }
        
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

def kirim_notifikasi_wa(nama_siswa, kelas, status, wa_ortu, file_path=None):
    import requests
    import os
    from datetime import datetime
    
    TOKEN_FONNTE = "tLLDYRoDrb2Rom19ohgp"
    
    waktu_sekarang = datetime.now().strftime("%H:%M") 
    tanggal_sekarang = datetime.now().strftime("%d-%m-%Y")
    
    # 1. Ambil template pesan dinamis dari DB
    config = ambil_pengaturan_geofencing()
    template_dari_admin = config["template_wa"]
    
    # 2. Masukkan data siswa ke dalam template
    pesan_custom = template_dari_admin
    pesan_custom = pesan_custom.replace("[nama]", nama_siswa)
    pesan_custom = pesan_custom.replace("[kelas]", kelas)
    pesan_custom = pesan_custom.replace("[jam]", waktu_sekarang)
    pesan_custom = pesan_custom.replace("[tanggal]", tanggal_sekarang)
    pesan_custom = pesan_custom.replace("[status]", status)
    
    # 3. ATUR ENDPOINT & PAYLOAD
    if file_path and os.path.exists(file_path):
        URL_FONNTE = "https://api.fonnte.com/send-media"
        payload = {
            'target': wa_ortu,
            'caption': pesan_custom, # Teks masuk ke 'caption' jika kirim media
            'countryCode': '62', 
        }
    else:
        URL_FONNTE = "https://api.fonnte.com/send"
        payload = {
            'target': wa_ortu,
            'message': pesan_custom, # Teks masuk ke 'message' jika teks biasa
            'countryCode': '62', 
        }
    
    headers = {
        'Authorization': TOKEN_FONNTE
    }
    
    # 4. Susun file dengan format tuple yang disukai oleh API Fonnte
    files = None
    if file_path and os.path.exists(file_path):
        try:
            nama_file_asli = os.path.basename(file_path)
            # Format tuple: (nama_file, file_binary, content_type)
            files = {
                'file': (nama_file_asli, open(file_path, 'rb'), 'image/jpeg')
            }
            print(f"📸 Menyertakan foto presensi ke WhatsApp: {file_path}")
        except Exception as e_file:
            print(f"⚠️ Gagal membaca file gambar {file_path}: {e_file}. Dialihkan ke teks saja.")
            URL_FONNTE = "https://api.fonnte.com/send"
            payload['message'] = pesan_custom
            files = None

    try:
        # Kirim request ke Fonnte
        response = requests.post(URL_FONNTE, headers=headers, data=payload, files=files)
        
        # Selalu tutup file setelah request selesai agar tidak terjadi memory leak/file terkunci
        if files:
            files['file'][1].close()
            
        # Cek jika server mengembalikan response sukses kosong atau error HTTP sebelum di-parse ke JSON
        if response.status_code == 200:
            try:
                response_data = response.json()
                if response_data.get("status"):
                    print(f"👉 [Fonnte] WhatsApp + Foto sukses dikirim ke nomor {wa_ortu}")
                    return True
                else:
                    print(f"❌ [Fonnte] Gagal kirim. Alasan: {response_data.get('reason')}")
                    return False
            except Exception as json_err:
                print(f"❌ [Fonnte] Gagal membaca response JSON: {response.text}")
                return False
        else:
            print(f"❌ [Fonnte] Server mengembalikan HTTP Status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        if files:
            files['file'][1].close()
        print(f"❌ [Fonnte] Error koneksi ke API Fonnte: {e}")
        return False
    
def simpan_template_wa(template_wa):
    """Khusus untuk menyimpan atau memperbarui template WA saja"""
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor()
            # Cek apakah sudah ada data konfigurasi geofencing sebelumnya
            cursor.execute("SELECT COUNT(*) FROM konfigurasi_geofencing")
            ada_data = cursor.fetchone()[0]
            
            if ada_data > 0:
                # Jika sudah ada koordinat geofencing, cukup update kolom template_wa
                sql = "UPDATE konfigurasi_geofencing SET template_wa = %s"
                val = (template_wa,)
            else:
                # Jika benar-benar kosong, insert baru dengan koordinat default SMA Sjakhyakirti
                sql = "INSERT INTO konfigurasi_geofencing (latitude, longitude, radius, template_wa) VALUES (%s, %s, %s, %s)"
                val = ("-2.994583", "104.756111", "100", template_wa)
                
            cursor.execute(sql, val)
            db.commit()
            return True
        except Exception as e:
            print(f">>> ERROR SIMPAN TEMPLATE WA: {e}")
            return False
        finally:
            cursor.close()
            db.close()
    return False

def hitung_wa_terkirim_hari_ini():
    """Mengambil jumlah riwayat absensi sukses hari ini (karena setiap absen sukses = 1 WA terkirim)"""
    conn = get_db_connection()
    jumlah = 0
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM catatan_kehadiran WHERE DATE(waktu_absen) = CURDATE()"
            cursor.execute(query)
            jumlah = cursor.fetchone()[0]
        except Exception as e:
            print(f">>> ERROR HITUNG WA TERKIRIM: {e}")
        finally:
            conn.close()
    return jumlah