import cv2
import numpy as np
import json
from deepface import DeepFace
from sklearn.preprocessing import normalize
import mysql.connector
from datetime import datetime
from database_connect import cek_presensi_hari_ini

# ============================================================
# KONFIGURASI 
# ============================================================
MODEL_NAME = "ArcFace"
DETECTOR = "mtcnn"
BEST_THRESHOLD = 0.35  

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="db_presensi_siswa" 
    )

class AbsenEngine:
    def __init__(self):
        self.known_embeddings = []
        self.known_names = []
        self.load_database_wajah()

    def cek_sudah_absen_hari_ini(self, id_siswa):
        db = get_db_connection()
        cursor = db.cursor()
        hari_ini = datetime.now().strftime('%Y-%m-%d')
        try:
            sql = "SELECT id_siswa FROM catatan_kehadiran WHERE id_siswa = %s AND DATE(waktu_absen) = %s"
            cursor.execute(sql, (id_siswa, hari_ini))
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            print(f"Error cek absen: {e}")
            return False
        finally:
            cursor.close()
            db.close()

    def load_database_wajah(self):
        """Mengambil semua embedding centroid dari MySQL ke memori"""
        db = get_db_connection()
        cursor = db.cursor()
        self.known_ids = []
        self.known_names = []
        self.known_embeddings = []
        
        try:
            cursor.execute("SELECT id_siswa, nama, face_embedding FROM dataset_siswa WHERE role = 'siswa' AND face_embedding IS NOT NULL")
            rows = cursor.fetchall()
            
            for row in rows: # --- LOOP DIMULAI ---
                id_s = row[0]
                nama = row[1]
                embedding_raw = row[2]
            
                try:
                    if isinstance(embedding_raw, str):
                        embedding_list = json.loads(embedding_raw)
                    else:
                        embedding_list = embedding_raw
                    
                    emb_np = np.array(embedding_list).astype('float32')
                    
                    if emb_np.shape == (512,):
                        self.known_ids.append(id_s)
                        self.known_names.append(nama)
                        self.known_embeddings.append(emb_np)
                        print(f">>> BERHASIL MEMUAT: {nama} (ID: {id_s})")
                    else:
                        print(f"[WARN] Data {nama} diabaikan karena ukuran salah: {emb_np.shape}")

                except Exception as e:
                    print(f"[WARN] Gagal memproses wajah {nama}: {e}")
            
            # Proses finalisasi setelah semua data masuk ke list
            if len(self.known_embeddings) > 0:
                self.known_embeddings = np.array(self.known_embeddings).astype('float32')
                if len(self.known_embeddings.shape) == 3:
                    self.known_embeddings = np.squeeze(self.known_embeddings, axis=1)
                
                self.known_embeddings = normalize(self.known_embeddings)
                print(f"--- TOTAL: Berhasil memuat {len(self.known_names)} data wajah siswa ---")
            else:
                print("[WARN] Database wajah kosong.")        

        except Exception as e:
            print(f"[ERROR] Database error: {e}")
        finally:
            cursor.close()
            db.close()

    def recognize_frame(self, frame, target_id):
        processed_frame = frame.copy()
        
        try:
            results = DeepFace.represent(
                img_path = frame,
                model_name = MODEL_NAME,
                detector_backend = DETECTOR,
                enforce_detection = True,
                align = True
            )

            for res in results:
                obj = res["facial_area"]
                x, y, w, h = obj['x'], obj['y'], obj['w'], obj['h']
                
                cv2.rectangle(processed_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # 3. Hitung Jarak (Distance)
                test_emb = np.array(res["embedding"]).reshape(1, -1)
                test_emb = normalize(test_emb)
                
                if len(self.known_embeddings) > 0:
                    # Menghitung similarity dulu
                    similarity = np.dot(test_emb, self.known_embeddings.T)[0]
                    best_idx = np.argmax(similarity)
                    
                    # Ubah ke Distance untuk disesuaikan dengan threshold 0.35 kamu
                    distance = float(1 - similarity[best_idx])
                    
                    id_terdeteksi = self.known_ids[best_idx]
                    nama_db = self.known_names[best_idx]
                    print(f"DEBUG: Terdeteksi={nama_db} (ID:{id_terdeteksi}), Target ID={target_id}, Dist={distance:.4f}")
                    
                    # Logika Threshold 0.35 (Makin kecil makin mirip)
                    if distance <= 0.35:
                        if str(id_terdeteksi) == str(target_id):
                            if distance <= 0.35:
                                if str(id_terdeteksi) == str(target_id):
                                    if cek_presensi_hari_ini(id_terdeteksi):
                                        msg = "SUDAH ABSEN"
                                    else:
                                        return True, f"{nama_db}|{distance}", processed_frame
                        else:
                            msg = "BUKAN PEMILIK AKUN"
                            color = (0, 0, 255) 
                    else:
                        msg = "WAJAH TIDAK DIKENALI"
                        color = (0, 0, 255)

                    # Tampilkan info di atas kotak
                    cv2.putText(processed_frame, f"{msg} ({distance:.2f})", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            return False, None, processed_frame

        except Exception as e:
            return False, None, processed_frame
    