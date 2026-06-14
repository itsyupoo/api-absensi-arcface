# views/siswa/presensi.py

import flet as ft
import cv2
import base64
import math
import time
import requests
from datetime import datetime
from components.ui import C, geo_indicator, chip
import importlib
import database_connect as db_conn
importlib.reload(db_conn)

STEPS = [
    "Mendeteksi wajah...",
    "Mengirim ke server...",
    "ArcFace memverifikasi identitas...",
    "Validasi koordinat GPS...",
    "Menyimpan ke database...",
    "Mengirim notifikasi WhatsApp...",
]

class SiswaPresensi:
    def __init__(self, page, state, go_to):
        self.page      = page
        self.state     = state
        self.go_to     = go_to
        self.geo_ok    = True
        self.capturing = False
        self.is_fake_gps = False

        self.geo_ref      = ft.Ref[ft.Container]()
        self.step_col_ref = ft.Ref[ft.Column]()
        self.btn_ref      = ft.Ref[ft.Container]()
        self.btn_text_ref = ft.Ref[ft.Text]()
        self.dlg_ref      = ft.Ref[ft.AlertDialog]()
        self.img_ref      = ft.Ref[ft.Image]()
        self.cam_sheet_ref = ft.Ref[ft.BottomSheet]()
        self.gps_text_ref = ft.Ref[ft.Text]()
        self.btn_absen_ref = ft.Ref[ft.Container]()
        self.camera_picker = ft.FilePicker(on_result=self.on_camera_result)
        self.page.overlay.append(self.camera_picker)
        self.res_nama_ref = ft.Ref[ft.Text]()
        self.res_jam_ref = ft.Ref[ft.Text]()
        self.res_status_ref = ft.Ref[ft.Text]()
        self.res_lokasi_ref = ft.Ref[ft.Text]()
        self.res_wa_ref = ft.Ref[ft.Text]()

        self.lat_terakhir = 0.0
        self.lon_terakhir = 0.0 
               
        self.geolocator = ft.Geolocator(
            on_error=lambda e: print(f"Geolocator error: {e.data}")
        )
        if self.geolocator not in self.page.overlay:
            self.page.overlay.append(self.geolocator)

    def hitung_jarak_haversine(self, lat1, lon1, lat2, lon2):
        """Menghitung jarak antara dua koordinat dalam satuan meter"""
        R = 6371000.0 
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def update_geo_ui(self):
        """Update tampilan indikator lokasi di dashboard"""
        if self.geo_ref.current:
            self.geo_ref.current.content = geo_indicator(self.geo_ok).content
            self.geo_ref.current.bgcolor = C["green_dim"] if self.geo_ok else C["red_dim"]
            self.geo_ref.current.border = ft.border.all(
                1, f"{C['green']}30" if self.geo_ok else f"{C['red']}30"
            )
            self.page.update()

    def toggle_geo(self, e):
        """Toggle lokasi (demo)"""
        self.is_fake_gps = not self.is_fake_gps
        
        if self.is_fake_gps:
            self.gps_text_ref.current.value = "✗ Terdeteksi"
            self.gps_text_ref.current.color = "red"
            self.btn_absen_ref.current.disabled = True
            self.btn_absen_ref.current.bgcolor = "grey"
            self.btn_text_ref.current.value = "🚫 Absen Terkunci (Fake GPS)"
            msg = "⚠️ Peringatan: Aplikasi Pemalsu Lokasi Terdeteksi!"
            color = "red"
        else:
            self.gps_text_ref.current.value = "✓ Aman"
            self.gps_text_ref.current.color = "green"
            self.btn_absen_ref.current.disabled = False
            self.btn_absen_ref.current.bgcolor = "#1A4BD4"
            self.btn_text_ref.current.value = "Ambil Foto & Verifikasi"
            msg = "Sistem Keamanan: Lokasi Terverifikasi Asli"
            color = "green"

        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor=color,
            duration=3000
        )
        self.page.snack_bar.open = True
        self.page.update()

    def run_real_process(self, e):
        if self.is_fake_gps:
            self.page.snack_bar = ft.SnackBar(ft.Text("Gagal: Matikan Fake GPS untuk melakukan absensi!"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
            return

        # LOGIKA PEMBATASAN 1 HARI 1X ABSEN
        try:
            session_id = self.page.session.get("user_id")
            id_target = int(session_id) if session_id else 0

            db = db_conn.get_db_connection()
            if db:
                cursor = db.cursor()
                tgl_sekarang = datetime.now().strftime("%Y-%m-%d")
                query = "SELECT COUNT(*) FROM catatan_kehadiran WHERE id_siswa = %s AND DATE(waktu_absen) = %s"
                cursor.execute(query, (id_target, tgl_sekarang))
                result = cursor.fetchone()
                
                cursor.close()
                db.close()
                
                if result and result[0] > 0:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Anda sudah melakukan absensi hari ini! Pembatasan: 1 hari hanya bisa 1x absen."), 
                        bgcolor="orange"
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    return 
        except Exception as check_ex:
            print(f"Gagal melakukan validasi pembatasan harian: {check_ex}")

        self.btn_text_ref.current.value = "📡 Mencari Sinyal GPS..."
        self.page.update()

        try:
            posisi_siswa = self.geolocator.get_current_position(accuracy="high")
            if posisi_siswa:
                self.lat_terakhir = float(posisi_siswa.latitude)
                self.lon_terakhir = float(posisi_siswa.longitude)
                
                from database_connect import ambil_pengaturan_geofencing
                data_sekolah = ambil_pengaturan_geofencing()
                
                lat_sekolah = float(data_sekolah["latitude"])
                lon_sekolah = float(data_sekolah["longitude"])
                radius_sekolah = float(data_sekolah["radius"])
                
                jarak = self.hitung_jarak_haversine(self.lat_terakhir, self.lon_terakhir, lat_sekolah, lon_sekolah)
                print(f"DEBUG GPS: Jarak ke Sekolah: {jarak:.2f} meter")
                
                if jarak <= radius_sekolah:
                    self.geo_ok = True
                    self.update_geo_ui()
                    self.jarak_terakhir = jarak 
                    self.do_capture(e)
                else:
                    self.geo_ok = False
                    self.update_geo_ui()
                    self._show_fail_dialog() 
        except Exception as ex:
            print(f"Gagal mengambil GPS HP: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text("Gagal mendapatkan lokasi. Pastikan GPS HP aktif!"), bgcolor="red")
            self.page.snack_bar.open = True
        finally:
            if not self.capturing:
                if self.btn_text_ref.current:
                    self.btn_text_ref.current.value = "📸 Ambil Foto & Verifikasi"
            self.page.update()
            
    def frame_to_base64(self, frame):
        try:
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            return jpg_as_text
        except Exception as e:
            print(f"Error konversi frame: {e}")
            return None
        
    def do_capture(self, e):
        print("DEBUG: Tombol ditekan!")
        if not self.geo_ok or self.capturing:
            return
        
        # Tambahkan 'file_type=ft.FilePickerFileType.IMAGE' 
        # dan pastikan browser tahu kita butuh akses kamera
        self.camera_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["jpg", "png", "jpeg"],
        )
    # Cukup hapus tipe data spesifiknya dan ganti dengan e saja
        def on_camera_result(self, e):
            # 3. Setelah foto diambil, baru kita tampilkan "preview" 
            # sebelum benar-benar dikirim ke API
            if e.files and e.files[0].path:
                path_foto = e.files[0].path
                
                # Di sini kamu bisa buat Dialog/Sheet untuk konfirmasi foto
                self.show_preview_dialog(path_foto)

    def show_preview_dialog(self, path_foto):
        # Tampilkan preview foto agar siswa merasa yakin fotonya sudah benar
        dlg = ft.AlertDialog(
            title=ft.Text("Konfirmasi Foto"),
            content=ft.Image(src=path_foto, width=300, height=300),
            actions=[
                ft.TextButton("Kirim Absen", on_click=lambda e: self.eksekusi_kirim(path_foto)),
                ft.TextButton("Batal", on_click=lambda e: self.close_dlg(e))
            ]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def eksekusi_kirim_final(self, path_foto):
        self.close_preview()
        
        # Tampilkan loading ke user
        self.page.snack_bar = ft.SnackBar(ft.Text("Mengirim foto ke server..."))
        self.page.snack_bar.open = True
        self.page.update()

        try:
            with open(path_foto, "rb") as file_foto:
                payload_files = {"file": ("selfie.jpg", file_foto, "image/jpeg")}
                payload_data = {
                    "id_siswa": str(self.state.get("user_data", {}).get("id_siswa")),
                    "latitude": float(self.lat_terakhir),
                    "longitude": float(self.lon_terakhir)
                }
                res = requests.post("http://192.168.1.23:8000/verify-presensi", data=payload_data, files=payload_files, timeout=30)
            
            # --- LOGIKA PENANGANAN RESPON ---
            hasil_api = res.json()
            if res.status_code == 200 and hasil_api.get("status") == "sukses":
                waktu_skrg = datetime.now()
                # Panggil dialog sukses
                self._show_success_dialog(
                    nama=str(self.state.get("user_data", {}).get("nama", "Siswa")),
                    jam=waktu_skrg.strftime("%H:%M WIB"),
                    status_hadir="Hadir",
                    status_wa=True,
                    distance=hasil_api.get("akurasi", 0)
                )
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Gagal: {hasil_api.get('message')}"), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()

        except Exception as err:
            print(f"Error kirim API: {err}")
            self.page.snack_bar = ft.SnackBar(ft.Text("Gagal terhubung ke server!"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()

    def _show_success_dialog(self, nama, jam, status_hadir, status_wa, distance):
        skor_formatted = f"{distance:.2f}% Match" if isinstance(distance, (int, float)) else str(distance)

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=C["surface"],
            shape=ft.RoundedRectangleBorder(radius=20),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Text("✅", size=40, text_align=ft.TextAlign.CENTER),
                            alignment="center", width=72, height=72, border_radius=36, bgcolor=C["green_dim"], border=ft.border.all(2, f"{C['green']}40"),
                        ),
                        ft.Text(
                            "Presensi Berhasil!",
                            size=18, weight=ft.FontWeight.W_800, color=C["green"], text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Wajah berhasil diverifikasi ArcFace Server.\nLaporan sukses masuk sistem cloud.", size=13, color=C["text2"], text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    self._detail_row("Nama", nama),
                                    self._detail_row("Jam Masuk", jam),
                                    self._detail_row("Status", status_hadir,
                                                     value_color=C["green"] if "Tepat" in status_hadir else "red"),
                                    self._detail_row("Lokasi", "✓ Radius Aman",
                                                     value_color=C["green"]),
                                    self._detail_row("ArcFace Score", skor_formatted, 
                                                     value_color=C["blue"]),
                                    self._detail_row("WA Gateway", 
                                                     "✓ Diproses Cloud" if status_wa else "✗ Gagal",
                                                     value_color=C["green"] if status_wa else "red"),
                                ],
                                spacing=0,
                            ),
                            bgcolor=C["surface2"], border_radius=10, border=ft.border.all(1, C["border"]), padding=12,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "Selesai", size=14, weight=ft.FontWeight.W_700, color="#FFFFFF", text_align=ft.TextAlign.CENTER,
                            ),
                            bgcolor=C["green"], border_radius=10, padding=ft.padding.symmetric(vertical=12),
                            on_click=lambda e: self._close_dialog(),
                            ink=True,
                        ),
                    ],
                    spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                width=300, padding=4,
            ),
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
        self._active_dlg = dlg

    def _close_dialog(self):
        self._active_dlg.open = False
        self.page.update()
        self.go_to("/siswa", tab=0)

    def _show_fail_dialog(self):
        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=C["surface"],
            shape=ft.RoundedRectangleBorder(radius=20),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Text("❌", size=36, text_align=ft.TextAlign.CENTER),
                            alignment="center", width=68, height=68, border_radius=34, bgcolor=C["red_dim"],border=ft.border.all(2, f"{C['red']}40"),
                        ),
                        ft.Text("Lokasi Tidak Valid", size=17,
                                weight=ft.FontWeight.W_800, color=C["red"],
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(
                            "Anda berada di luar radius sekolah.\nPresensi hanya bisa dilakukan di area sekolah.",
                            size=12, color=C["text2"],
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(
                            content=ft.Text("Tutup", size=13,
                                            weight=ft.FontWeight.W_700, color=C["red"], text_align=ft.TextAlign.CENTER),
                            bgcolor=C["red_dim"],border_radius=10,
                            border=ft.border.all(1, f"{C['red']}40"),
                            padding=ft.padding.symmetric(vertical=10),
                            on_click=lambda e: self._close_fail(),
                            ink=True,
                        ),
                    ],
                    spacing=12,horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                width=280,padding=4,
            ),
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
        self._fail_dlg = dlg

    def _close_fail(self):
        self._fail_dlg.open = False
        self.page.update()

    def _detail_row(self, key, val, value_color=None):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(key, size=12, color=C["text2"], expand=True),
                    ft.Text(val, size=12, weight=ft.FontWeight.W_600,
                            color=value_color or C["text"]),
                ]
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, C["border"])),
            padding=ft.padding.symmetric(vertical=6),
        )

    def build(self) -> ft.Container:
        step_rows = []
        for s in STEPS:
            step_rows.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=8, height=8,border_radius=99,bgcolor=C["border2"],
                        ),
                        ft.Text(s, size=12, color=C["text2"]),
                    ],
                    spacing=10,vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        step_col = ft.Column(
            ref=self.step_col_ref,
            controls=step_rows,
            spacing=6,
            visible=False,
        )

        geo_cont = ft.Container(
            ref=self.geo_ref,
            content=geo_indicator(True).content, bgcolor=C["green_dim"], border_radius=8,
            border=ft.border.all(1, f"{C['green']}30"),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            margin=ft.margin.only(bottom=12),
        )

        cam_box = ft.Container(
            content=ft.Stack(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("📷", size=40, text_align=ft.TextAlign.CENTER),
                                ft.Text("Kamera selfie real-time",
                                        size=12, color=C["text3"],
                                        text_align=ft.TextAlign.CENTER),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        alignment="center",
                        expand=True,
                    ),
                    ft.Container(
                        width=110, height=110,
                        border_radius=55,
                        border=ft.border.all(2, f"{C['blue']}60"),
                        alignment="center",
                    ),
                ],
                alignment="center",
            ),
            height=260,
            bgcolor=C["surface2"],
            border_radius=12,
            border=ft.border.all(1, C["border"]),
            margin=ft.margin.only(bottom=14),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        capture_btn = ft.Container(
            ref=self.btn_absen_ref,
            content=ft.Row(
                controls=[
                    ft.Icon("camera_alt_outlined", color="white"),
                    ft.Text(
                        "Ambil Foto & Verifikasi", 
                        ref=self.btn_text_ref,
                        size=14, 
                        weight=ft.FontWeight.W_600, 
                        color="white"
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor="#1A4BD4",
            padding=ft.padding.symmetric(vertical=16),
            border_radius=12,
            on_click=self.run_real_process,
            ink=True,
        )

        gps_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("GPS Asli (Anti-Mock)", size=12, color=C["text2"], expand=True),
                    ft.Text(
                        ref=self.gps_text_ref,
                        value="✓ Aman" if not self.is_fake_gps else "✗ Terdeteksi",
                        size=12, weight=ft.FontWeight.W_700,
                        color=C["green"] if not self.is_fake_gps else C["red"],
                    ),
                ]
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, C["border"])),
            padding=ft.padding.symmetric(vertical=7),
        )
        
        other_checks = [
            ("VPN Aktif",           True),
        ]
        other_rows = [
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(lbl, size=12, color=C["text2"], expand=True),
                        ft.Text(
                            "✓ Aman" if ok else "✗ Terdeteksi",
                            size=12, weight=ft.FontWeight.W_700,
                            color=C["green"] if ok else C["red"],
                        ),
                    ]
                ),
                border=ft.border.only(bottom=ft.BorderSide(1, C["border"])),
                padding=ft.padding.symmetric(vertical=7),
            )
            for lbl, ok in other_checks
        ]
        
        integrity_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("🛡️ Integritas Perangkat", size=13,
                                    weight=ft.FontWeight.W_700, color=C["text"]),
                        ]
                    ),
                    ft.Container(height=8),
                    gps_row,
                    *other_rows,
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Text(
                            "Toggle Lokasi GPS (Demo)",
                            size=12, weight=ft.FontWeight.W_600,
                            color=C["text2"],
                            text_align=ft.TextAlign.CENTER,
                        ),
                        border_radius=8,
                        border=ft.border.all(1, C["border2"]),
                        padding=ft.padding.symmetric(horizontal=14, vertical=8),
                        on_click=self.toggle_geo,
                        ink=True,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=C["surface"],
            border_radius=12,
            border=ft.border.all(1, C["border"]),
            padding=16,
            margin=ft.margin.only(bottom=12),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text("Verifikasi Presensi", size=15,
                                        weight=ft.FontWeight.W_700, color=C["text"],
                                        expand=True),
                                chip("Selfie Mode", "blue"),
                            ],
                        ),
                        bgcolor=C["surface"],
                        border=ft.border.only(
                            bottom=ft.BorderSide(1, C["border"])
                        ),
                        padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=4),
                                geo_cont,
                                cam_box,
                                step_col,
                                capture_btn,
                                integrity_card,
                                ft.Container(height=16),
                            ],
                            spacing=0,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        expand=True,
                        padding=ft.padding.symmetric(horizontal=16),
                    ),
                ],
                spacing=0,
            ),
            expand=True,
            bgcolor=C["bg"],
        )