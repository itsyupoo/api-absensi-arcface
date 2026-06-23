# views/siswa/presensi.py

import flet as ft
import base64
import math
import time
import requests
from datetime import datetime
from components.ui import C, geo_indicator, chip
import importlib
import database_connect as db_conn
importlib.reload(db_conn)
import platform
print(platform.system())
import os


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
        self.camera_picker = ft.FilePicker()
        self.page.services.append(self.camera_picker)
        self.res_nama_ref = ft.Ref[ft.Text]()
        self.res_jam_ref = ft.Ref[ft.Text]()
        self.res_status_ref = ft.Ref[ft.Text]()
        self.res_lokasi_ref = ft.Ref[ft.Text]()
        self.res_wa_ref = ft.Ref[ft.Text]()
        self.jarak_terakhir = None
        self.lat_terakhir = 0.0
        self.lon_terakhir = 0.0 
        self.lokasi_siap = False
        self._active_dlg = None
        self._fail_dlg = None

    def hitung_jarak_haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000.0 
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def get_location(self):
        print("WEB MODE")

        self.on_location_callback(
            lat=-3.0360034410727312,
            lon=104.75166409564264
        )

    def on_location_callback(self, **kwargs):
        print("GPS CALLBACK DIPANGGIL")
        print("DATA GPS =", kwargs)

        lat = kwargs.get("lat")
        lon = kwargs.get("lon")

        print("LAT =", lat)
        print("LON =", lon)

        if lat is not None and lon is not None:
            self.lat_terakhir = float(lat)
            self.lon_terakhir = float(lon)
                       
            from database_connect import ambil_pengaturan_geofencing
            data_sekolah = ambil_pengaturan_geofencing()
            print("DATA SEKOLAH =", data_sekolah)
            
            jarak = self.hitung_jarak_haversine(
                self.lat_terakhir, self.lon_terakhir, 
                float(data_sekolah["latitude"]), float(data_sekolah["longitude"])
            )
            print("JARAK =", jarak)
            print("RADIUS =", data_sekolah["radius"])

            if jarak <= float(data_sekolah["radius"]):
                print("MASUK SUKSES GEOGENCING")
                self.geo_ok = True
                self.jarak_terakhir = round(jarak, 2)
                self.update_geo_ui()
                self.buka_pilihan_foto(None)
            else:
                print("MASUK FAIL GEOFENCING")
                self.geo_ok = False
                self.jarak_terakhir = round(jarak, 2)
                self.update_geo_ui()

                self._show_fail_dialog(
                    f"Lokasi Tidak Valid.\nJarak Anda {round(jarak,2)} meter dari sekolah."
                )
            self.page.update()
        else:
            print("GPS TIDAK MEMBERIKAN KOORDINAT")    

    def update_geo_ui(self):
        if self.geo_ref.current:
            self.geo_ref.current.content = geo_indicator(self.geo_ok).content
            self.geo_ref.current.bgcolor = C["green_dim"] if self.geo_ok else C["red_dim"]
            self.geo_ref.current.border = ft.border.all(
                1, f"{C['green']}30" if self.geo_ok else f"{C['red']}30"
            )
            self.page.update()

    def toggle_geo(self, e):
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

        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=color, duration=3000)
        self.page.open(snack)
        self.page.update()

    def run_real_process(self, e):
        print("TOMBOL PRESENSI DIKLIK")

        print("PLATFORM PAGE =", self.page.platform)
        print("ANDROID?", self.page.platform == ft.PagePlatform.ANDROID)

        try:
            print("WEB =", self.page.web)
        except Exception as err:
            print("WEB TIDAK ADA =", err)

        print("PAGE ATTR =", [x for x in dir(self.page) if "web" in x.lower()])
        
        self.geo_ok = False
        self.update_geo_ui()

        print("=== CEK GEO ===")
        print([x for x in dir(self.page) if "location" in x.lower()])
        print([x for x in dir(self.page) if "geo" in x.lower()])
        self.get_location()
   
    def buka_pilihan_foto(self, e):
        print("BOTTOMSHEET DIBUKA")
        self.bs = ft.BottomSheet(
            content=ft.Container(
                padding=20,
                content=ft.Column(tight=True,
                    controls=[ft.Text("Pilih Sumber Foto",size=18,weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.ListTile(leading=ft.Icon(ft.Icons.CAMERA_ALT),title=ft.Text("Ambil Selfie"),subtitle=ft.Text(    "Gunakan kamera perangkat"),
                            on_click=self.fitur_kamera
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.PHOTO_LIBRARY),
                            title=ft.Text("Pilih dari Galeri"),
                            subtitle=ft.Text(    "Pilih foto yang sudah ada"),
                            on_click=self.pilih_dari_galeri
                        ),
                        ft.Divider(),
                        ft.TextButton("Batal",on_click=self.tutup_bottomsheet)
                    ])
            )
        )
        self.bs.open = True
        self.page.show_dialog(self.bs)

    def tutup_bottomsheet(self, e):
        print("TUTUP BOTTOMSHEET")
        self.bs.open = False
        self.page.update()

    async def fitur_kamera(self, e):
        files = await self.camera_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["jpg", "jpeg", "png"],
            with_data=True
        )

        print(files)

        if files:
            self._snack(
                f"FILE: {files[0].name}",
                color="green"
            )

    async def pilih_dari_galeri(self, e):
        self.bs.open = False
        self.page.update()
        files = await self.camera_picker.pick_files(
            allow_multiple=False,allowed_extensions=["jpg", "jpeg", "png"])
        print("FILES =", files)
        if not files:
            print("TIDAK ADA FILE")
            return
        
        print(type(files[0]))
        print(files[0].__dict__)

        print("FILE0 =", files[0])
        print("DIR =", dir(files[0]))
        print("PATH =", getattr(files[0], "path", None))
        print("NAME =", getattr(files[0], "name", None))
        print("BYTES =", getattr(files[0], "bytes", None))

        path_foto = files[0].path
        print("PATH FOTO =", path_foto)
        self.show_preview_dialog(path_foto)
        print("SHOW PREVIEW DIPANGGIL")

    async def do_capture(self, e):
        if not self.geo_ok or self.capturing:
            return
        print("Tombol ambil foto ditekan")
        files = await self.camera_picker.pick_files(
            allow_multiple=False,allowed_extensions=["jpg", "jpeg", "png"])
        print("pick_files selesai")
        print(files)

    def show_preview_dialog(self, path_foto):
        print(">>> SHOW PREVIEW DIALOG")
        self.preview_dialog = ft.AlertDialog(
            title=ft.Text("Konfirmasi Foto"),
            content=ft.Image(src=path_foto,width=300,height=300),
            actions=[
                ft.TextButton(
                    "Kirim",on_click=lambda e: self.eksekusi_kirim_final(path_foto)),
                ft.TextButton(
                    "Batal",on_click=self.tutup_preview_dialog)
            ])
        self.page.show_dialog(self.preview_dialog)

    def tutup_preview_dialog(self, e):
        self.page.pop_dialog()
        self.page.update()

    def show_loading_dialog(self):
        self.loading_dialog = ft.AlertDialog(
            modal=True,
            bgcolor=C["surface"],
            content=ft.Container(
                width=280,
                padding=20,
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(),
                        ft.Text(
                            "Memverifikasi Presensi...",
                            size=14,
                            weight=ft.FontWeight.W_600,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Mohon tunggu, sistem sedang memproses wajah dan lokasi Anda.",
                            size=11,
                            color=C["text2"],
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
            ),
        )

        self.page.show_dialog(self.loading_dialog)

    def close_loading_dialog(self):
        try:
            self.page.pop_dialog()
            self.page.update()
            print("LOADING DITUTUP")

        except Exception as err:
            print("ERROR CLOSE LOADING =", err)

    def eksekusi_kirim_final(self, path_foto):
        print("=== MULAI KIRIM KE RAILWAY ===")
        
        self.page.pop_dialog()
        self.page.update()
       
        self.show_loading_dialog()
        try:
            print("USER DATA =", self.state.get("user_data"))
            print("LAT =", self.lat_terakhir)
            print("LON =", self.lon_terakhir)
            with open(path_foto, "rb") as foto:
                data = {
                    "id_siswa": str(
                        self.state["user_data"]["id_siswa"]
                    ),
                    "nama_siswa": str(
                        self.state["user_data"]["nama"]
                    ),
                    "latitude": str(
                        self.lat_terakhir
                    ),
                    "longitude": str(
                        self.lon_terakhir
                    )
                }
                files = {
                    "file": (
                        "selfie.jpg",
                        foto,
                        "image/jpeg"
                    )
                }
                print("KIRIM KE RAILWAY...")
                response = requests.post(
                    "https://sjakhyakirtibackendapi-production.up.railway.app/verify-presensi",
                    data=data,
                    files=files,
                    timeout=60
                )
            print("STATUS =", response.status_code)
            print("RESPONSE =", response.text)
            hasil_api = response.json()
            # ====================================
            # BERHASIL
            # ====================================
            if response.status_code == 200:
                # refresh dashboard siswa
                self.state["dashboard_refresh"] = True
                self.close_loading_dialog()
                waktu_skrg = datetime.now()
                self._show_success_dialog(
                    nama=str(
                        self.state["user_data"]["nama"]
                    ),
                    jam=waktu_skrg.strftime("%H:%M WIB"),
                    status_hadir=hasil_api.get(
                        "status_kehadiran",
                        "-"
                    ),
                    status_wa=hasil_api.get(
                        "status_wa",
                        False
                    ),
                    distance=hasil_api.get(
                        "akurasi",
                        0
                    )
                )

            # ====================================
            # GAGAL
            # ====================================
            else:
                print("TUTUP LOADING")
                self.close_loading_dialog()
                print("LOADING DITUTUP")
                self._show_fail_dialog(
                    hasil_api.get(
                        "message",
                        "Presensi gagal."
                    )
                )
        except Exception as err:
            print("ERROR =", err)
            self.close_loading_dialog()
            self._show_fail_dialog(
                "Gagal terhubung ke server Railway."
            )
                
    def _show_success_dialog(self, nama, jam, status_hadir, status_wa, distance):
        print(">>> SHOW SUCCESS DIALOG")
        skor_formatted = f"{distance:.4f}" if isinstance(distance, (int, float)) else str(distance)
        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=C["surface"],
            shape=ft.RoundedRectangleBorder(radius=20),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "✅",
                            size=40,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "Presensi Berhasil!",
                            size=18,
                            weight=ft.FontWeight.W_800,
                            color=C["green"],
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Wajah berhasil diverifikasi ArcFace Server.\nLaporan sukses masuk sistem cloud.",
                            size=13,
                            color=C["text2"],
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    self._detail_row("Nama", nama),
                                    self._detail_row("Jam Masuk", jam),
                                    self._detail_row("Status", status_hadir, value_color=C["green"]
                                                     if "Tepat" in status_hadir else "red"),
                                    self._detail_row("Lokasi", "✓ Radius Aman", value_color=C["green"]),
                                    self._detail_row("Cosine Distance", skor_formatted, value_color=C["blue"]),       
                                    self._detail_row("WA Gateway", "✓ Terkirim" if status_wa else "✗ Gagal", value_color=C["green"] if status_wa else "red"),      
                                ],
                                spacing=0,
                            ),
                            bgcolor=C["surface2"],
                            border_radius=10,
                            border=ft.border.all(1, C["border"]),
                            padding=12,
                        ),
                        ft.TextButton(
                            content=ft.Container(
                                width=220,
                                bgcolor=C["green"],
                                border_radius=10,
                                padding=ft.Padding(
                                    top=10,
                                    bottom=10
                                ),
                                content=ft.Text(
                                    "Selesai",
                                    size=13,
                                    weight=ft.FontWeight.W_700,
                                    color="#FFFFFF",
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ),
                            on_click=lambda e: self._close_success_dialog(e)
                        )
                    ],
                    spacing=12, 
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    tight=True,
                ),
                width=300, 
                padding=4,
            ),
        )
        self._active_dlg = dlg
        self.page.show_dialog(dlg)

    def _close_success_dialog(self, e):
        print("TUTUP SUCCESS")

        try:
            self.page.pop_dialog()
            self.page.update()
        except Exception as err:
            print("ERROR =", err)

    def _show_fail_dialog(self, pesan):
        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=C["surface"],
            content=ft.Container(
                width=280,
                height=180,
                padding=20,
                content=ft.Column(
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "❌",
                            size=36,
                            text_align=ft.TextAlign.CENTER,
                        ),

                        ft.Text(
                            "Presensi Gagal",
                            size=17,
                            weight=ft.FontWeight.W_800,
                            color=C["red"],
                            text_align=ft.TextAlign.CENTER,
                        ),

                        ft.Text(
                            pesan,
                            size=12,
                            color=C["text2"],
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.TextButton(
                            "Tutup",
                            on_click=lambda e: (
                                print("TOMBOL TUTUP DIKLIK"),
                                self._close_fail_dialog(e)
                            )
                        )
                    ],
                    tight=True,
                ),
            ),
        )
        self._fail_dlg = dlg
        self.page.show_dialog(dlg)

    def _close_fail_dialog(self, e):
        print("MASUK CLOSE FAIL DIALOG")

        try:
            self.page.pop_dialog()
            self.page.update()
        except Exception as err:
            print("ERROR CLOSE =", err)

    def _detail_row(self, key, val, value_color=None):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(key, size=12, color=C["text2"], expand=True),
                    ft.Text(val, size=12, weight=ft.FontWeight.W_600, color=value_color or C["text"]),
                ]
            ),
            border=ft.Border(bottom=ft.BorderSide(1, C["border"])),
            padding=ft.Padding(top=6, bottom=6),
        )

    def build(self) -> ft.Container:
        step_rows = []
        for s in STEPS:
            step_rows.append(
                ft.Row(
                    controls=[
                        ft.Container(width=8, height=8, border_radius=99, bgcolor=C["border2"]),
                        ft.Text(s, size=12, color=C["text2"]),
                    ],
                    spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
            padding=ft.Padding(left=12,right=12,top=8,bottom=8),
            margin=ft.Margin(bottom=12),
        )

        cam_box = ft.Container(
            height=250,
            bgcolor=C["surface2"],
            border_radius=12,
            border=ft.border.all(1, C["border"]),
            margin=ft.Margin(bottom=14),
            padding=20,
            on_click=self.run_real_process, 
            content=ft.Column( 
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("📷", size=40),
                    ft.Text("Ambil Foto dan Verifikasi Kehadiran", size=12, color="black"),
                ]
            )
        )
        
        gps_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("GPS Asli (Anti-Mock)", size=12, color=C["text2"], expand=True),
                    ft.Text(ref=self.gps_text_ref, value="✓ Aman" if not self.is_fake_gps else "✗ Terdeteksi", size=12, weight=ft.FontWeight.W_700, color=C["green"] if not self.is_fake_gps else C["red"]),
                ]
            ),
            border=ft.Border(bottom=ft.BorderSide(1, C["border"])),
            padding=ft.Padding(top=7,bottom=7),
        )
        
        other_checks = [("VPN Aktif", True)]
        other_rows = [
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(lbl, size=12, color=C["text2"], expand=True),
                        ft.Text("✓ Aman" if ok else "✗ Terdeteksi", size=12, weight=ft.FontWeight.W_700, color=C["green"] if ok else C["red"]),
                    ]
                ),
                border=ft.Border(bottom=ft.BorderSide(1, C["border"])),
                padding=ft.Padding(top=7,bottom=7),
            ) for lbl, ok in other_checks
        ]
        
        integrity_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([ft.Text("🛡️ Integritas Perangkat", size=13, weight=ft.FontWeight.W_700, color=C["text"])]),
                    ft.Container(height=8),
                    gps_row,
                    *other_rows,
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Text("Toggle Lokasi GPS (Demo)", size=12, weight=ft.FontWeight.W_600, color=C["text2"], text_align=ft.TextAlign.CENTER),
                        border_radius=8, border=ft.border.all(1, C["border2"]), padding=ft.Padding(left=14,right=14,top=8,bottom=8),
                        on_click=self.toggle_geo, ink=True,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=C["surface"], border_radius=12, border=ft.border.all(1, C["border"]), padding=16, margin=ft.Margin(bottom=12),
        )

        return ft.Container(
            expand=True,
            bgcolor=C["bg"], # Background asli kamu
            content=ft.SafeArea(
                content=ft.Column(
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        # 1. Header
                        ft.Container(
                            bgcolor=C["surface"],
                            border=ft.Border(bottom=ft.BorderSide(1, C["border"])),
                            padding=16,
                            content=ft.Row([
                                ft.Text("Verifikasi Presensi", size=15, weight=ft.FontWeight.W_700, color=C["text"], expand=True), 
                                chip("Selfie Mode", "blue")
                            ]),
                        ),
                        
                        # 2. ListView (Area Isi)
                        ft.ListView(
                            expand=True,
                            padding=16,
                            spacing=12,
                            controls=[
                                geo_cont,
                                cam_box,
                                integrity_card,
                            ]
                        ) 
                    ]
                )
            )
        )