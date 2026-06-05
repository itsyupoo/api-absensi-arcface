# views/admin/settings.py

import flet as ft
import requests
from components.ui import C, chip, wa_status_bar, section_title


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
                ft.Text(label.upper(), size=10, weight=ft.FontWeight.W_700, color=C["text2"]),
                ft.TextField(
                    ref=ref,
                    value=value,
                    hint_text=hint,
                    on_change= on_change,
                    bgcolor=C["surface2"],
                    border_color=C["border2"],
                    focused_border_color=C["blue"],
                    color=C["text"],
                    hint_style=ft.TextStyle(color=C["text3"]),
                    border_radius=8,
                    content_padding=ft.padding.symmetric(
                        horizontal=12, vertical=8
                    ),
                ),
            ],
            spacing=4,
            expand=True,
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
                C["border2"] if color == "ghost" else f"{C.get(color, C['blue'])}40",
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            on_click=on_click,
            ink=True,
            expand=True,
        )
    def _update_map_realtime(self, e):
        lat = self.ref_lat.current.value if self.ref_lat.current else "-2.994583"
        lng = self.ref_lng.current.value if self.ref_lng.current else "104.756111"
              
        new_map_url = f"https://static-maps.yandex.ru/1.x/?lang=en_US&ll={lng},{lat}&z=16&l=map&pt={lng},{lat},pm2rdm"
        if self.ref_map_img.current:
            self.ref_map_img.current.src = new_map_url
            self.page.update()

    def _ambil_status_fonnte_realtime(self):
        """Helper untuk mendapatkan status Fonnte API & data DB secara akurat"""
        from database_connect import hitung_wa_terkirim_hari_ini
        TOKEN_FONNTE = "tLLDYRoDrb2Rom19ohgp"
        total_hari_ini = hitung_wa_terkirim_hari_ini()
        
        try:
            # 👉 PERBAIKAN: Gunakan requests.post dengan header Authorization yang benar
            # Serta pastikan endpoint-nya merespon balik dengan tepat
            response = requests.post(
                "https://api.fonnte.com/device", 
                headers={"Authorization": TOKEN_FONNTE},
                timeout=5
            )
            res_data = response.json()
            
            # Print log ke terminal untuk mempermudah kamu debugging isi respon Fonnte
            print(f" LOG FONNTE API: {res_data}")
            
            # Fonnte mengembalikan status: true/false, dan detail di dalam key 'device_status' atau 'status'
            if res_data.get("status") == True or res_data.get("device_status") == "connected":
                return "Terhubung Fonnte API", "green", True, f"{total_hari_ini} pesan dikirim hari ini"
            else:
                # Jika token salah atau nomor tidak aktif di server
                return "Terputus dari Fonnte", "red", False, f"{total_hari_ini} pesan dikirim hari ini"
                
        except Exception as e:
            print(f"❌ Error saat cek API Fonnte: {e}")
            return "Gagal Cek API Fonnte", "orange", False, f"{total_hari_ini} pesan dikirim hari ini"

    def proses_simpan_geo(self, e=None):
        from database_connect import simpan_pengaturan_geofencing
        lat = self.ref_lat.current.value
        lng = self.ref_lng.current.value
        rad = self.ref_radius.current.value
        
        if simpan_pengaturan_geofencing(lat, lng, rad):
            self._snack("✅ Konfigurasi Geofencing tersimpan!")
        else:
            self._snack("❌ Gagal menyimpan konfigurasi.")

        self.page.update()

    def proses_simpan_template_wa(self, e=None):
        """Fungsi baru hasil pemisahan tombol khusus simpan template teks WA"""
        from database_connect import simpan_template_wa
        template_text = self.ref_wa_template.current.value

        if not template_text:
            self._snack("⚠️ Template pesan tidak boleh kosong!")
            return

        if simpan_template_wa(template_text):
            self._snack("✅ Template WhatsApp berhasil diperbarui!")
        else:
            self._snack("❌ Gagal menyimpan template ke database.")
        self.page.update()

    def proses_simpan_keamanan(self, e=None):
        from database_connect import simpan_keamanan_sistem
        anti_mock = self.ref_mock_mode.current.value
        emulator = self.ref_emulator_mode.current.value # Pastikan ref ini sudah ada
        root_check = self.ref_root_mode.current.value   # Pastikan ref ini sudah ada

        if simpan_keamanan_sistem(anti_mock, emulator, root_check):
            self._snack("✅ Konfigurasi keamanan berhasil diperbarui!")
        else:
            self._snack("❌ Gagal menyimpan keamanan.")
        
        self.page.update()

    def build(self) -> ft.Container:
        from database_connect import ambil_pengaturan_geofencing
        data_db = ambil_pengaturan_geofencing()

        geo_lat = data_db.get("latitude", "-2.994583")
        geo_lng = data_db.get("longitude", "104.756111")
        geo_rad = data_db.get("radius", "100")
        
        # Nilai Token Fonnte dan Template Pesan dinamis dari DB
        wa_template_val = data_db.get(
            "template_wa", 
            "Halo Orang Tua Siswa, menginfokan bahwa siswa atas nama {nama} telah hadir di sekolah pada {jam}."
        )

        status_device, warna_chip, is_active, total_wa_info = self._ambil_status_fonnte_realtime()

        # ── Geofencing card ──
        geo_card = ft.Container(
            bgcolor=C["surface"], border_radius=12, border=ft.border.all(1, C["border"]), padding=16, margin=ft.margin.only(bottom=12),
            content=ft.Column(
                spacing=12,
                controls=[
                    section_title("📍 Konfigurasi Geofencing"),
                    ft.Container(
                        alignment=ft.alignment.center,
                        bgcolor=C["surface2"], # Ini aman karena berada di dalam kontainer yang berbeda
                        border_radius=10,
                        border=ft.border.all(1, C["border"]),
                        height=280, padding=10,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Image(
                                    ref=self.ref_map_img,
                                    src=f"https://static-maps.yandex.ru/1.x/?lang=en_US&ll=104.756111,-2.994583&z=16&l=map&pt=104.756111,-2.994583,pm2rdm", width=550, height=250,  fit=ft.ImageFit.CONTAIN,  border_radius=10, 
                             ),
                        ],
                    ),
                ),
                    
                    # 3. Row Latitude & Longitude
                    ft.Row(
                        controls=[
                            self._field("Latitude", "-2.994583", ref=self.ref_lat, on_change=self._update_map_realtime),
                            ft.Container(width=10),
                            self._field("Longitude", "104.756111", ref=self.ref_lng, on_change=self._update_map_realtime),
                        ],
                    ),

                    ft.Container(height=8),

                    # 4. Row Radius & Mock GPS
                    ft.Row(
                        controls=[
                            self._field("Radius (meter)", "100", ref=self.ref_radius),
                            ft.Container(width=10),
                            ft.Column(
                                expand=True,spacing=4,
                                controls=[
                                    ft.Text("MOCK GPS".upper(), size=10, weight=ft.FontWeight.W_700, color=C["text2"]),
                                    ft.Dropdown(
                                        ref=self.ref_mock_mode,
                                        options=[ft.dropdown.Option("Aktif"), ft.dropdown.Option("Nonaktif")],
                                        value="Aktif", bgcolor=C["surface2"], border_radius=8, color=C["text"],
                                        content_padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    self._action_btn("💾 Simpan Geofencing", "blue", self.proses_simpan_geo),
                    ],
            ),
        )

        wa_card = ft.Container(
            bgcolor=C["surface"], border_radius=12, border=ft.border.all(1, C["border"]), padding=16, margin=ft.margin.only(bottom=12),
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
                        border=ft.border.all(1, C["border2"])
                    ),
                    ft.Container(height=10),
                    ft.Column([
                        ft.Text("TEMPLATE PESAN WA", size=10, weight=ft.FontWeight.W_700, color=C["text2"]),
                        ft.TextField(ref=self.ref_wa_template, value=wa_template_val, bgcolor=C["surface2"], color=C["text"], multiline=True, min_lines=3, border_radius=8),
                    ], spacing=4),
                    ft.Container(height=12),
                    # 👉 TOMBOL DIUBAH MENJADI SIMPAN TEMPLATE
                    self._action_btn("💾 Simpan Template WA", "blue", self.proses_simpan_template_wa),
                ],
            ),
        )
    
        sec_card = ft.Container(
            bgcolor=C["surface"], border_radius=12, border=ft.border.all(1, C["border"]), padding=16, margin=ft.margin.only(bottom=12),
            content=ft.Column(
                spacing=15,
                controls=[
                    section_title("🛡️ Keamanan Sistem"),
                    ft.Row([
                        ft.Text("Emulator Detection", expand=True, color=C["text2"]),
                        ft.Dropdown(ref=self.ref_emulator_mode, options=[ft.dropdown.Option("Aktif"), ft.dropdown.Option("Nonaktif")], 
                                    value="Aktif", width=120, bgcolor=C["surface2"], color=C["text"])
                    ]),
                    ft.Row([
                        ft.Text("Root/Jailbreak Check", expand=True, color=C["text2"]),
                        ft.Dropdown(ref=self.ref_root_mode, options=[ft.dropdown.Option("Aktif"), ft.dropdown.Option("Nonaktif")], 
                                    value="Aktif", width=120, bgcolor=C["surface2"], color=C["text"])
                    ]),
                    ft.Divider(color=C["border"]),
                    self._action_btn("💾 Simpan Keamanan", "blue", self.proses_simpan_keamanan),
                ],
            ),
        )

        return ft.Container(
            expand=True, bgcolor=C["bg"],
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text("Pengaturan", size=15, weight=ft.FontWeight.W_700, color=C["text"]),
                        bgcolor=C["surface"], padding=16, border=ft.border.only(bottom=ft.BorderSide(1, C["border"])),
                    ),
                    ft.Container(
                        expand=True, padding=14,
                        content=ft.Column([geo_card, wa_card, sec_card, ft.Container(height=20)], scroll=ft.ScrollMode.AUTO),
                    ),
                ],
                spacing=0,
            ),
        )