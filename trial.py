# views/siswa/presensi.py

import flet as ft
import cv2
import base64
from components.ui import C, card, geo_indicator, chip
from absen_engine import AbsenEngine

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
        
        self.res_nama_ref = ft.Ref[ft.Text]()
        self.res_jam_ref = ft.Ref[ft.Text]()
        self.res_status_ref = ft.Ref[ft.Text]()
        self.res_lokasi_ref = ft.Ref[ft.Text]()
        self.res_wa_ref = ft.Ref[ft.Text]()

    def update_geo_ui(self):
        """Update tampilan indikator lokasi di dashboard"""
        if self.geo_ref.current:
            self.geo_ref.current.content = geo_indicator(self.geo_ok).content
            self.geo_ref.current.bgcolor = C["green_dim"] if self.geo_ok else C["red_dim"]
            self.geo_ref.current.border = ft.border.all(
                1, f"{C['green']}30" if self.geo_ok else f"{C['red']}30"
            )
            self.page.update()

    # ── Toggle lokasi (demo) ──
    def toggle_geo(self, e):
        self.is_fake_gps = not self.is_fake_gps
        
        if self.is_fake_gps:
            # Skenario TERDETEKSI (Kunci Tombol)
            self.gps_text_ref.current.value = "✗ Terdeteksi"
            self.gps_text_ref.current.color = "red"
            
            self.btn_absen_ref.current.disabled = True
            self.btn_absen_ref.current.bgcolor = "grey", 400 # Ubah jadi abu-abu
            self.btn_text_ref.current.value = "🚫 Absen Terkunci (Fake GPS)"
            
            msg = "⚠️ Peringatan: Aplikasi Pemalsu Lokasi Terdeteksi!"
            color = "red"
        else:
            # Skenario AMAN (Buka Tombol)
            self.gps_text_ref.current.value = "✓ Aman"
            self.gps_text_ref.current.color = "green"
            
            self.btn_absen_ref.current.disabled = False
            self.btn_absen_ref.current.bgcolor = "#1A4BD4" # Kembali ke biru
            self.btn_text_ref.current.value = "Ambil Foto & Verifikasi"
            
            msg = "Sistem Keamanan: Lokasi Terverifikasi Asli"
            color = "green"

        # Tampilkan Snackbar
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor=color,
            duration=3000
        )
        self.page.snack_bar.open = True
        self.page.update()

        # 3. Munculkan notifikasi di bawah
        msg = "Peringatan: Pemalsuan Lokasi Terdeteksi!" if self.is_fake_gps else "Sistem Keamanan: Normal"
        # Ganti ft.colors.RED jadi "red" dan ft.colors.GREEN jadi "green"
        self.page.snack_bar = ft.SnackBar(ft.Text(msg),bgcolor="red" if self.is_fake_gps else "green"
)
        self.page.snack_bar.open = True
        
        self.page.update()

    def run_real_process(self, e):
        # 1. Cek proteksi GPS (Fitur baru)
        if self.is_fake_gps:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Gagal: Matikan Fake GPS untuk melakukan absensi!"),
                bgcolor="red"
            )
            self.page.snack_bar.open = True
            self.page.update()
            return # Berhenti di sini, kamera gak akan terbuka

        # 2. Kalau GPS aman, panggil fungsi kamera kamu yang lama
        self.do_capture(e)

    def frame_to_base64(self, frame):
        try:
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            return jpg_as_text
        except Exception as e:
            print(f"Error konversi frame: {e}")
            return None
        
    # ── Proses capture step-by-step ──
    def do_capture(self, e):
        if not self.geo_ok:
            self._show_fail_dialog()
            return
        if self.capturing:
            return
        
        self.capturing = True
        self.btn_text_ref.current.value = "⏳ Inisialisasi Kamera..."
        self.page.update()

        self.cam_sheet = ft.BottomSheet(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            height=4, width=50, bgcolor=C["border"], border_radius=10,
                            alignment=ft.alignment.center
                        ),
                        ft.Text("Verifikasi Wajah", size=16, weight="bold"),
                        ft.Text("Posisikan wajah Anda di dalam lingkaran", size=12, color=C["text2"]),
                        ft.Container(
                            content=ft.Stack([
                                ft.Image(ref=self.img_ref, width=320, height=320, fit="cover"),
                            ], alignment=ft.alignment.center),
                            border_radius=20,
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        ),
                        ft.Text("Sedang memproses...", italic=True, size=12),
                    ],
                    tight=True, horizontal_alignment="center", spacing=15,
                ),
                padding=25, bgcolor=C["surface"], border_radius=ft.border_radius.only(top_left=20, top_right=20),
            ),
            is_scroll_controlled=True,
            enable_drag=False, 
        )
        
        self.page.overlay.append(self.cam_sheet)
        self.cam_sheet.open = True
        self.page.update()
        import threading
        # Kita buat fungsi pembantu kecil untuk menjalankan isi logika kameramu
        threading.Thread(target=self.execute_camera_logic, daemon=True).start()

    def execute_camera_logic(self):
        import time
        from datetime import datetime
        engine = AbsenEngine()
        cap = cv2.VideoCapture(0)
        id_target = self.page.session.get("user_id") 
            
        print(f"DEBUG: Memulai verifikasi untuk ID: {id_target}")

        if not cap.isOpened():
            print("Error: Kamera tidak ditemukan")
            self.capturing = False
            return
            
        status_absen = False
        nama_siswa = ""

        try:
             start_time = time.time()
             while self.capturing: # Gunakan flag capturing sebagai kontrol loop
                ret, frame = cap.read()
                if not ret: break

                durasi = time.time() - start_time
                    
                if durasi < 2.0:
                    display_frame = frame.copy()
                    cv2.putText(display_frame, f"Menyiapkan Kamera... {int(3-durasi)}", 
                                (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                else:
                    status, nama, output_frame = engine.recognize_frame(frame, id_target)
                    display_frame = output_frame 
                        
                    if status:
                        print(f"✅ BERHASIL MENDETEKSI: {nama}")
                        nama_siswa = nama
                        status_absen = True
                        break

                if self.img_ref.current:
                    self.img_ref.current.src_base64 = self.frame_to_base64(display_frame)
                    self.page.update()

        except Exception as ex:
            print(f"Error di Thread Kamera: {ex}")

        finally:
             cap.release()
             self.capturing = False 
             if hasattr(self, 'cam_sheet'):
                self.cam_sheet.open = False
             self.page.update()

             if status_absen:
                time.sleep(0.3)
                waktu_skrg = datetime.now()
                self._show_success_dialog(
                    nama=nama_siswa, 
                    jam=waktu_skrg.strftime("%H:%M WIB"), 
                    status_hadir="Hadir Tepat Waktu" if waktu_skrg.hour < 7 else "Terlambat", 
                    status_wa=True
                )
             else:
                if self.btn_text_ref.current:
                    self.btn_text_ref.current.value = "📸 Ambil Foto & Verifikasi"
                self.page.update()

    def _show_success_dialog(self, nama, jam, status_hadir, status_wa):
        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=C["surface"],
            shape=ft.RoundedRectangleBorder(radius=20),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Text("✅", size=40,
                                            text_align=ft.TextAlign.CENTER),
                            alignment=ft.alignment.center,width=72, height=72, border_radius=36, bgcolor=C["green_dim"], border=ft.border.all(2, f"{C['green']}40"),
                        ),
                        ft.Text(
                            "Presensi Berhasil!",
                            size=18, weight=ft.FontWeight.W_800, color=C["green"], text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Wajah berhasil diverifikasi ArcFace.\nLaporan dikirim ke orang tua via WhatsApp.", size=13, color=C["text2"], text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    self._detail_row("Nama", nama),
                                    self._detail_row("Jam Masuk", jam),
                                    self._detail_row("Status", status_hadir,
                                                     value_color=C["green"] if "Tepat" in status_hadir else "red"),
                                    self._detail_row("Lokasi", "✓ Dalam Area",
                                                     value_color=C["green"]),
                                    self._detail_row("WA Ortu", 
                                                     "✓ Terkirim" if status_wa else "✗ Gagal",
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
                    spacing=12,horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                width=300,padding=4,
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
                            content=ft.Text("❌", size=36,
                                            text_align=ft.TextAlign.CENTER),
                            alignment=ft.alignment.center, width=68, height=68, border_radius=34, bgcolor=C["red_dim"],border=ft.border.all(2, f"{C['red']}40"),
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
        # Step tracker
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

        # Geo indicator container
        geo_cont = ft.Container(
            ref=self.geo_ref,
            content=geo_indicator(True).content, bgcolor=C["green_dim"], border_radius=8,
            border=ft.border.all(1, f"{C['green']}30"),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            margin=ft.margin.only(bottom=12),
        )

        # Camera box
        cam_box = ft.Container(
            content=ft.Stack(
                controls=[
                    # Placeholder
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
                        alignment=ft.alignment.center,
                        expand=True,
                    ),
                    # Face ring hint
                    ft.Container(
                        width=110, height=110,
                        border_radius=55,
                        border=ft.border.all(2, f"{C['blue']}60"),
                        alignment=ft.alignment.center,
                    ),
                ],
                alignment=ft.alignment.center,
            ),
            height=260,
            bgcolor=C["surface2"],
            border_radius=12,
            border=ft.border.all(1, C["border"]),
            margin=ft.margin.only(bottom=14),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,

        )
        # Capture button
        btn_label = ft.Text(
            ref=self.btn_text_ref,
            value="📸 Ambil Foto & Verifikasi",
            size=15, weight=ft.FontWeight.W_800,
            color="#FFFFFF",
            text_align=ft.TextAlign.CENTER,
        )
        capture_btn = ft.Container(
            ref=self.btn_absen_ref, # Pastikan ref ini terpasang
            content=ft.Row(
                controls=[
                    ft.Icon("camera_alt_outlined", color="white"),
                    ft.Text(
                        "Ambil Foto & Verifikasi", 
                        ref=self.btn_text_ref, # Pasang ref juga di teksnya
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
            on_click=self.run_real_process, # Ini fungsi yang membuka kamera
            ink=True,
        )

        # Integrity checks card
        gps_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("GPS Asli (Anti-Mock)", size=12, color=C["text2"], expand=True),
                    ft.Text(
                        ref=self.gps_text_ref, # PASANG REF DI SINI
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
                    # Topbar
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

                    # Body
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
