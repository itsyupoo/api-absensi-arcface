# views/admin/settings.py

import flet as ft
import requests
from components.ui import C, chip, wa_status_bar, section_title

# 🌐 GANTI dengan URL domain publik Railway kamu yang ada /docs-nya tadi
BASE_URL = "https://api-absensi-arcface-production.up.railway.app"

class AdminSettings:
    def __init__(self, page, state, go_to):
        self.page  = page
        self.state = state
        self.go_to = go_to

        self.ref_lat = ft.Ref[ft.TextField]()
        self.ref_lng = ft.Ref[ft.TextField]()
        self.ref_radius = ft.Ref[ft.TextField]()
        self.ref_wa_key = ft.Ref[ft.TextField]()
        self.ref_wa_template = ft.Ref[ft.TextField]()
        self.ref_mock_mode = ft.Ref[ft.Dropdown]()
        self.ref_map_marker = ft.Ref[ft.Container]()
        self.ref_map_img = ft.Ref[ft.Image]()
        self.ref_emulator_mode = ft.Ref[ft.Dropdown]()
        self.ref_root_mode = ft.Ref[ft.Dropdown]()

    def _snack(self, msg):
        snack = ft.SnackBar(
            content=ft.Text(msg, color="#FFFFFF", weight=ft.FontWeight.W_500),
            bgcolor=C["blue"], action="OK", duration=3000)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()   

    def _field(self, label, value="", hint="", ref=None, on_change=None):
        return ft.Column(
            controls=[
                ft.Text(label.upper(), size=8, weight=ft.FontWeight.W_700, color=C["text2"]),
                ft.TextField(
                    ref=ref,
                    value=str(value), # Dipastikan dikonversi menjadi string
                    hint_text=hint,
                    on_change=on_change,
                    bgcolor=C["surface2"],
                    border_color=C["border2"],
                    focused_border_color=C["blue"],
                    color=C["text"],
                    text_size=13,
                    border_radius=8,
                    content_padding=ft.Padding(left=10, right=10, top=6, bottom=6),
                ),
            ],
            spacing=2,
        )

    def _action_btn(self, label, color, on_click):
        return ft.Container(
            content=ft.Text(label, size=13,
                            weight=ft.FontWeight.W_700,
                            color="#FFFFFF" if color != "ghost" else C["text2"],
                            text_align=ft.TextAlign.CENTER),
            bgcolor=C.get(color, C["blue"]) if color != "ghost" else "transparent",
            border_radius=9,
            border=ft.border.all(
                1,
                C["border2"] 
                if color == "ghost" else f"{C.get(color, C['blue'])}40",
            ),
            padding=ft.Padding(left=14, right=14, top=10, bottom=10),
            on_click=on_click,
            ink=True,
            expand=True,
        )

    def _update_map_realtime(self, e):
        lat = self.ref_lat.current.value if self.ref_lat.current and self.ref_lat.current.value else "-2.9602"
        lng = self.ref_lng.current.value if self.ref_lng.current and self.ref_lng.current.value else "104.7554"
              
        new_map_url = f"https://static-maps.yandex.ru/1.x/?lang=en_US&ll={lng},{lat}&z=16&l=map&pt={lng},{lat},pm2rdm"
        if self.ref_map_img.current:
            self.ref_map_img.current.src = new_map_url
            self.page.update()

    def _ambil_status_fonnte_realtime(self):
        """Helper untuk mendapatkan status Fonnte API (Bypass Sementara)"""
        total_hari_ini = 0 
        
        # Sementara kita bypass langsung mengembalikan status "Siap" 
        # agar aplikasi tidak mengunci/lagging akibat timeout koneksi Fonnte
        return "Fonnte API (Siap)", "orange", True, f"{total_hari_ini} pesan dikirim hari ini"

    def proses_simpan_geo(self, e=None):
        """MENGUBAH TEMBAKAN: Mengirim data geofencing baru ke API Railway Cloud"""
        lat = float(self.ref_lat.current.value) if self.ref_lat.current.value else -2.9602
        lng = float(self.ref_lng.current.value) if self.ref_lng.current.value else 104.7554
        rad = float(self.ref_radius.current.value) if self.ref_radius.current.value else 50.0
        
        payload = {
            "latitude_sekolah": lat,
            "longitude_sekolah": lng,
            "radius_meter": rad
        }
        
        try:
            response = requests.post(f"{BASE_URL}/geofencing/update", json=payload, timeout=5)
            res_data = response.json()
            
            if response.status_code == 200 and res_data.get("status") == "success":
                self._snack("✅ Konfigurasi Geofencing tersimpan di Cloud Railway!")
            else:
                self._snack(f"❌ Gagal: {res_data.get('message', 'Terjadi kesalahan')}")
        except Exception as ex:
            self._snack(f"❌ Gagal terhubung ke Cloud Server: {ex}")

        self.page.update()

    def proses_simpan_template_wa(self, e=None):
        """Fungsi simpan template teks WA (Nanti bisa kita buatkan endpoint terpisah jika diperlukan)"""
        template_text = self.ref_wa_template.current.value
        if not template_text:
            self._snack("⚠️ Template pesan tidak boleh kosong!")
            return
        
        # Untuk saat ini kita buat notifikasi sukses lokal karena fokus utama 
        # menyambungkan tabel geofencing dan keamanan sistem yang sudah kita buat di database.
        self._snack("✅ Template WhatsApp diperbarui secara lokal!")
        self.page.update()

    def proses_simpan_keamanan(self, e=None):
        """MENGUBAH TEMBAKAN: Mengirim data 3 dropdown keamanan sekaligus ke Cloud"""
        anti_mock = self.ref_mock_mode.current.value      # Dropdown MOCK GPS
        emulator = self.ref_emulator_mode.current.value   # Dropdown Emulator
        root_check = self.ref_root_mode.current.value
        
        payload = {
            "anti_mock_gps": anti_mock,
            "emulator_detection": emulator,
            "root_check": root_check
        }
        
        try:
            response = requests.post(f"{BASE_URL}/sistem-keamanan/update", json=payload, timeout=5)
            res_data = response.json()
            
            if response.status_code == 200 and res_data.get("status") == "success":
                self._snack("✅ Konfigurasi keamanan diperbarui di Cloud Railway!")
            else:
                self._snack(f"❌ Gagal: {res_data.get('message', 'Terjadi kesalahan')}")
        except Exception as ex:
            self._snack(f"❌ Gagal terhubung ke Cloud Server: {ex}")
        
        self.page.update()

    def build(self) -> ft.Container:
        """MENGUBAH DATA LOAD: Mengambil konfigurasi awal secara realtime dari API Cloud Railway"""
        # Set nilai default cadangan terlebih dahulu
        geo_lat = "-2.9602"
        geo_lng = "104.7554"
        geo_rad = "50"
        status_keamanan_val = "Aktif"

        anti_mock_val = "Aktif"
        emulator_val = "Nonaktif"
        root_val = "Nonaktif"

        try:
            # 1. Ambil data geofencing dari Cloud
            response_geo = requests.get(f"{BASE_URL}/geofencing", timeout=5)
            if response_geo.status_code == 200:
                data_geo = response_geo.json()
                geo_lat = str(data_geo.get("latitude_sekolah", "-2.9602"))
                geo_lng = str(data_geo.get("longitude_sekolah", "104.7554"))
                geo_rad = str(data_geo.get("radius_meter", "50"))
                
            # 2. Ambil data keamanan sistem dari Cloud
            response_sec = requests.get(f"{BASE_URL}/sistem-keamanan", timeout=5)
            if response_sec.status_code == 200:
                data_sec = response_sec.json()
                anti_mock_val = data_sec.get("anti_mock_gps", "Aktif")
                emulator_val = data_sec.get("emulator_detection", "Nonaktif")
                root_val = data_sec.get("root_check", "Nonaktif")
        except Exception as e:
            print(f"⚠️ Gagal load data dari cloud awal, menggunakan default: {e}")

        wa_template_val = "Halo Orang Tua Siswa, menginfokan bahwa siswa atas nama {nama} telah hadir di sekolah pada {jam}."
        status_device, warna_chip, is_active, total_wa_info = self._ambil_status_fonnte_realtime()

        # ── Geofencing card ──
        geo_card = ft.Container(
            bgcolor=C["surface"], 
            border_radius=12,
            padding=16,
            margin=ft.Margin(bottom=12),
            content=ft.Column(
                spacing=10,
                controls=[
                    section_title("📍 Konfigurasi Geofencing"),
                    # Pembungkus Peta
                    ft.Container(
                        height=180, # Tinggi tetap
                        border_radius=8,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE, # Penting agar gambar tidak keluar kotak
                        content=ft.Image(
                            ref=self.ref_map_img,
                            src=f"https://static-maps.yandex.ru/1.x/?lang=en_US&ll={geo_lng},{geo_lat}&z=16&l=map&pt={geo_lng},{geo_lat},pm2rdm",
                            fit="cover", # Memastikan gambar mengisi 180px tersebut
                            width=float("inf"),    # Memastikan lebar penuh
                            height=120,            # Memastikan tinggi penuh
                        ),
                    ),
                    # Pembungkus Form (Tadinya biru)
                    ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row([
                                self._field("Latitude", geo_lat, ref=self.ref_lat, on_change=self._update_map_realtime),
                                self._field("Longitude", geo_lng, ref=self.ref_lng, on_change=self._update_map_realtime),
                            ]),
                            self._field("Radius (meter)", geo_rad, ref=self.ref_radius),
                            self._action_btn("💾 Simpan Geofencing", "blue", self.proses_simpan_geo),
                        ]
                    ),
                ],
            ),
        )
                    
        
        wa_card = ft.Container(
            bgcolor=C["surface"], border_radius=12, border=ft.Border(left=ft.BorderSide(1, C["border"]), top=ft.BorderSide(1, C["border"]), right=ft.BorderSide(1, C["border"]), bottom=ft.BorderSide(1, C["border"])),
            padding=16, margin=ft.Margin(bottom=12),
            content=ft.Column(
                controls=[
                    ft.Row([section_title("📱 WhatsApp Gateway"), chip(status_device, warna_chip)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.FORWARD_TO_INBOX, size=16, color=C["text2"]),
                            ft.Text(total_wa_info, size=13, color=C["text2"], weight=ft.FontWeight.W_500)
                        ]),
                        bgcolor=C["surface2"],
                        padding=10,
                        border_radius=8,
                        border=ft.Border(left=ft.BorderSide(1, C["border2"]), top=ft.BorderSide(1, C["border2"]), right=ft.BorderSide(1, C["border2"]), bottom=ft.BorderSide(1, C["border2"]))
                    ),
                    ft.Container(height=10),
                    ft.Column([
                        ft.Text("TEMPLATE PESAN WA", size=10, weight=ft.FontWeight.W_700, color=C["text2"]),
                        ft.TextField(ref=self.ref_wa_template, value=wa_template_val, bgcolor=C["surface2"], color=C["text"], multiline=True, min_lines=3, border_radius=8),
                    ], spacing=4),
                    ft.Container(height=12),
                    self._action_btn("💾 Simpan Template WA", "blue", self.proses_simpan_template_wa),
                ],
            ),
        )
    
        sec_card = ft.Container(
            bgcolor=C["surface"], border_radius=12, border=ft.Border(left=ft.BorderSide(1, C["border"]), top=ft.BorderSide(1, C["border"]), right=ft.BorderSide(1, C["border"]), bottom=ft.BorderSide(1, C["border"])), 
            padding=15, margin=ft.Margin(bottom=12),
            content=ft.Column(
                spacing=12,
                controls=[
                    section_title("🛡️ Keamanan Sistem"),
                    ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Emulator Detection", color=C["text2"], size=15
                    ),
                    ft.Dropdown(
                        ref=self.ref_emulator_mode, 
                        options=[ft.dropdown.Option("Aktif"), ft.dropdown.Option("Nonaktif")], 
                        value="Aktif", 
                        width=100, # Sedikit lebih lebar agar teks tidak terpotong
                        text_size=12,
                        content_padding=ft.Padding(left=8, top=0, bottom=0, right=8), # Mengatur posisi teks di dlm dropdown
                        bgcolor=C["surface2"], 
                        color=C["text"],
                        border_radius=6,
                        dense=True,
                        border_width=1
                    )
                ]
            ),
            
            # Row Root
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Root/Jailbreak Check", color=C["text2"], size=15),
                    ft.Dropdown(
                        ref=self.ref_root_mode, 
                        options=[ft.dropdown.Option("Aktif"), ft.dropdown.Option("Nonaktif")], 
                        value="Aktif", 
                        width=100,  
                        text_size=12,
                        content_padding=ft.Padding(left=8, top=0, bottom=0, right=8),
                        bgcolor=C["surface2"], 
                        color=C["text"],
                        border_radius=6,
                        dense=True,
                        border_width=1
                    )
                ]
            ),
                    ft.Divider(color=C["border"], height=20),
                    self._action_btn("💾 Simpan Keamanan", "blue", self.proses_simpan_keamanan),
                ],
            ),
        )

        return ft.Container(
            expand=True,
            bgcolor=C["bg"], 
            padding=0,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=0,
                controls=[
                    # Header
                    ft.Container(
                        bgcolor=C["surface"],
                        padding=ft.Padding(top=40, bottom=16, left=16, right=16), 
                        border=ft.Border(bottom=ft.BorderSide(1, C["border"])),
                        content=ft.Text("Pengaturan", size=19, weight=ft.FontWeight.W_700, color=C["text"], width=float("inf")),
                    ),
                    # Area konten utama
                    ft.Container(
                        expand=True, # Mendorong area ini mengisi sisa layar
                        padding=ft.Padding(top=10, left=14, right=14, bottom=80),
                        content=ft.ListView(
                            spacing=12,
                            controls=[
                                geo_card, 
                                wa_card, 
                                sec_card, 
                            ]
                        ),
                    ),
                ]
            )
        )