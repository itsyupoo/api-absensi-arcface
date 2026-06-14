# views/admin/monitoring.py

import flet as ft
import threading
import time
from database_connect import ambil_presensi_terbaru, get_db_connection, hitung_wa_terkirim_hari_ini
from components.ui import C, chip, wa_status_bar, section_title

class AdminMonitoring:
    def __init__(self, page, state, go_to):
        self.page  = page
        self.state = state
        self.go_to = go_to

        self.log_container_ref = ft.Ref[ft.Column]()
        self.search_field_ref = ft.Ref[ft.TextField]()
        
        self.running = True
        threading.Thread(target=self._auto_refresh_task, daemon=True).start()

    def handle_logout(self, e):
        self.stop()
        self.state["user_data"] = {}
        self.go_to("/login")


    def _auto_refresh_task(self):
        """Thread untuk memperbarui data setiap 5 detik secara otomatis"""
        while self.running:
            if self.search_field_ref.current and not self.search_field_ref.current.value:
                self._load_data_to_ui()
            time.sleep(5)

    def _load_data_to_ui(self, search_name=None):
        """Mengambil data dari DB dan merender ulang list di UI"""
        if search_name:
            # Jika ada pencarian, ambil semua riwayat siswa tersebut
            logs = self._ambil_riwayat_siswa_spesifik(search_name)
        else:
            # Jika tidak ada pencarian, ambil 10 presensi terbaru hari ini
            logs = ambil_presensi_terbaru(limit=10)

        rows = []
        for res in logs:
            # Mapping status ke warna
            status_color = "green" if res['status'] == "Hadir" else "red"
            jam = res['waktu_absen'].strftime("%H:%M") if hasattr(res['waktu_absen'], 'strftime') else str(res['waktu_absen'])
            
            # Jika ini data riwayat (pencarian), mungkin ingin menampilkan tanggal juga
            sub_info = res['kelas']
            if search_name and hasattr(res['waktu_absen'], 'strftime'):
                sub_info = f"{res['kelas']} • {res['waktu_absen'].strftime('%d %b %Y')}"

            jk = res.get('jenis_kelamin', 'L')

            rows.append(self._create_log_row(
                nama=res['nama'], 
                kelas=sub_info, 
                jam=jam, 
                status=res['status'], 
                cls_color=status_color,
                jenis_kelamin=jk
            ))

        if self.log_container_ref.current:
            self.log_container_ref.current.controls = rows
            self.page.update()

    def _ambil_riwayat_siswa_spesifik(self, nama):
        """Fungsi internal untuk mencari riwayat kehadiran berdasarkan nama"""
        conn = get_db_connection()
        hasil = []
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                query = """
                    SELECT s.nama, s.kelas, s.jenis_kelamin, c.waktu_absen,
                           CASE WHEN TIME(c.waktu_absen) <= '07:15:00' THEN 'Hadir' ELSE 'Terlambat' END as status
                    FROM catatan_kehadiran c
                    JOIN dataset_siswa s ON c.id_siswa = s.id_siswa
                    WHERE s.nama LIKE %s
                    ORDER BY c.waktu_absen DESC
                """
                cursor.execute(query, (f"%{nama}%",))
                hasil = cursor.fetchall()
            finally:
                conn.close()
        return hasil

    def _create_log_row(self, nama, kelas, jam, status, cls_color, jenis_kelamin):
        from components.ui import C, chip 

        if jenis_kelamin in ["L", "Laki-laki", "Laki-Laki"]:
            path_avatar = "logo_cowok.png"
        else:
            path_avatar = "logo_cewek.png"

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Image(src=path_avatar,fit="contain",width=24,height=24,
                        ),
                        width=35, height=35, bgcolor=C["surface2"], border_radius=8, 
                        alignment="center"
                    ),
                    ft.Column([
                        ft.Text(nama, size=13, weight="bold", color=C["text"]),
                        ft.Text(kelas, size=11, color=C["text2"])
                    ], expand=True, spacing=1),
                    ft.Text(f"{jam} WIB", size=11, color=C["text2"], font_family="monospace"),
                    chip(status, cls_color)
                ]
            ),
            padding=ft.Padding(top=10, bottom=10, left=0, right=0),
            border=ft.Border(bottom=ft.BorderSide(1, C["border"]))
        )

    def build(self) -> ft.Container:
        self.log_list_column = ft.Column(ref=self.log_container_ref, spacing=0)
        self._load_data_to_ui()

        search_box = ft.TextField(
            ref=self.search_field_ref,
            hint_text="Cari nama siswa untuk riwayat...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda e: self._load_data_to_ui(e.control.value),
            bgcolor=C["surface2"], border_color=C["border2"], focused_border_color=C["blue"], color=C["text"],  hint_style=ft.TextStyle(color=C["text3"]),
            border_radius=8, content_padding=ft.Padding(left=12, right=12, top=8, bottom=8), expand=True)

        log_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            section_title("📡 Log Real-time"),
                            chip("● Live", "green"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        controls=[
                            search_box, # Gunakan search_box yang sudah dibuat di atas
                            ft.Dropdown(
                                options=[
                                    ft.dropdown.Option("Semua"),
                                    ft.dropdown.Option("Hadir"),
                                    ft.dropdown.Option("Terlambat"),
                                ],
                                value="Semua",
                                bgcolor=C["surface2"],
                                border_color=C["border2"],
                                border_radius=8,
                                width=120,
                                content_padding=ft.Padding(left=10, right=10, top=0, bottom=0),
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Container(height=8),
                    self.log_list_column,
                ]
            ),
            bgcolor=C["surface"],
            border_radius=12,
            border=ft.border.all(1, C["border"]),
            padding=16,
            margin=ft.Margin(bottom=12),
        )

        total_hari_ini = hitung_wa_terkirim_hari_ini()

        wa_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            section_title("📱 Status Gateway"),
                            chip("Aktif", "green"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=10),
                    wa_status_bar(active=True, total_pesan=total_hari_ini),
                    ft.Container(height=10),
                    ft.Row(
                        controls=[
                            self._mini_stat(str(total_hari_ini), "Terkirim", "green"), # 👈 Jadi Real-time!
                            self._mini_stat("0",  "Pending",  "blue"),
                            self._mini_stat("0",  "Gagal",    "red"),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=C["surface"],
            border_radius=12,
            border=ft.border.all(1, C["border"]),
            padding=16,
            margin=ft.Margin(bottom=12),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text("Monitoring Real-time", size=15, weight="bold", color=C["text"], expand=True),
                            ],
                        ),
                        bgcolor=C["surface"],
                        border=ft.Border(bottom=ft.BorderSide(1, C["border"])),
                        padding=ft.Padding(left=16, right=16, top=40, bottom=12),
                        width=float("inf")
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=4),
                                log_card,
                                wa_card,
                                ft.Container(height=16),

                                ft.Container(
                                    content=ft.Text(
                                        "Keluar / Logout",
                                        size=14, weight=ft.FontWeight.W_700,
                                        color="#FFFFFF",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    bgcolor="#0D47A1",
                                    border_radius=12,
                                    border=ft.border.all(1, f"{C['red']}40" if "red" in C else "#D32F2F"),
                                    padding=ft.Padding(top=13, bottom=13, right=0, left=0),
                                    
                                    # 👉 PANGGIL FUNGSI LOGOUT KAMU DI SINI:
                                    on_click=self.handle_logout,

                                    ink=True,
                                    margin=ft.Margin(bottom=24),
                                ),
                            ],
                            spacing=0, scroll=ft.ScrollMode.AUTO,
                        ),
                        expand=True,
                        padding=ft.Padding(left=14, right=14, top=0, bottom=0),
                    ),
                ],
                spacing=0,
            ),
            expand=True,
            bgcolor=C["bg"],
        )

    def _mini_stat(self, num, label, color):
        fg = C.get(color, C["blue"])
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(num, size=20, weight="bold", color=fg),
                    ft.Text(label, size=10, color=C["text2"]),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=C["surface2"], border_radius=10,  padding=10, expand=True)
    
    def stop(self):
        self.running = False

         