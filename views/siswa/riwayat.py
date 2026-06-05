# views/siswa/riwayat.py

import flet as ft
from components.ui import C, card, chip, stat_box
from database_connect import get_db_connection, ambil_statistik_siswa
from datetime import datetime


class SiswaRiwayat:
    def __init__(self, page, state, go_to):
        self.page  = page
        self.state = state
        self.go_to = go_to

        self.box_hadir = stat_box("0", "Hadir", "blue")
        self.box_telat = stat_box("0", "Terlambat", "warn")
        self.box_alfa  = stat_box("0", "Alfa", "red")
        self.box_persen = stat_box("0%", "Tingkat", "green")
        
        # Container untuk daftar log
        self.log_list_container = ft.Column(spacing=0)

    def get_indonesia_day(self, date_obj):
        days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        return days[date_obj.weekday()]
    
    def get_indonesia_month(self, date_obj):
        months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"]
        return months[date_obj.month - 1]
    
    def load_data(self):
        """Mengambil data dari database dan memperbarui UI"""
        user_id = self.state.get("user_id")
        if not user_id:
            return

        stats = ambil_statistik_siswa(user_id)
        self.box_hadir.content.controls[0].value = str(stats["hadir"])
        self.box_telat.content.controls[0].value = str(stats["terlambat"])
        # Alfa diset 0 atau bisa dihitung jika ada total hari efektif
        self.box_alfa.content.controls[0].value = "0" 
        self.box_persen.content.controls[0].value = stats["persen"]

        self.log_list_container.controls.clear()
        db = get_db_connection()
        if db:
            try:
                cursor = db.cursor(dictionary=True)
                # Query mengambil semua riwayat absen siswa ini
                query = """
                    SELECT status_kehadiran, waktu_absen 
                    FROM catatan_kehadiran 
                    WHERE id_siswa = %s 
                    ORDER BY waktu_absen DESC
                """
                cursor.execute(query, (user_id,))
                results = cursor.fetchall()

                for row in results:
                    dt = row['waktu_absen'] # Objek datetime
                    tgl = dt.day
                    bln = self.get_indonesia_month(dt)
                    hari = self.get_indonesia_day(dt)
                    jam = dt.strftime("%H:%M")
                    status = row['status_kehadiran']
                    
                    # Tentukan warna chip berdasarkan status di database
                    color_map = {
                        "Hadir": "green",
                        "Terlambat": "yellow",
                        "Izin": "blue",
                        "Sakit": "orange",
                        "Alfa": "red"
                    }
                    cls_color = color_map.get(status, "gray")

                    # Tambahkan ke daftar UI
                    self.log_list_container.controls.append(
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    # Kotak Tanggal
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
                                                ft.Text(str(tgl), size=18, weight="bold", color=C["text"]),
                                                ft.Text(bln, size=9, weight="bold", color=C["text3"]),
                                            ],
                                            spacing=0,
                                            horizontal_alignment="center",
                                        ),
                                        width=42, height=46,
                                        bgcolor=C["surface2"],
                                        border_radius=10,
                                        border=ft.border.all(1, C["border"]),
                                        alignment=ft.alignment.center,
                                    ),
                                    # Info Hari dan Jam
                                    ft.Column(
                                        controls=[
                                            ft.Text(hari, size=13, weight="w600", color=C["text"]),
                                            ft.Text(jam, size=11, color=C["text2"], font_family="monospace"),
                                        ],
                                        spacing=1,
                                        expand=True,
                                    ),
                                    # Status Badge
                                    chip(status, cls_color),
                                ],
                                spacing=12,
                                vertical_alignment="center",
                            ),
                            border=ft.border.only(bottom=ft.BorderSide(1, C["border"])),
                            padding=ft.padding.symmetric(vertical=10),
                        )
                    )
            except Exception as e:
                print(f"Error Load Riwayat: {e}")
            finally:
                db.close()

    def build(self) -> ft.Container:
        self.load_data()
        rekap_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(f"📊 Rekap {datetime.now().strftime('%B %Y')}", 
                                size=14, weight="bold", color=C["text"], expand=True),
                            chip("Aktif", "green"),
                        ]
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            self.box_hadir, self.box_telat, self.box_alfa, self.box_persen
                        ],
                        spacing=8,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=C["surface"],border_radius=12,
            border=ft.border.all(1, C["border"]),padding=16,margin=ft.margin.only(bottom=12),
        )

        log_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("📋 Log Harian", size=14,weight=ft.FontWeight.W_700, color=C["text"]),
                    ft.Container(height=8),
                    self.log_list_container,
                ],
                spacing=0,
            ),
            bgcolor=C["surface"],border_radius=12,
            border=ft.border.all(1, C["border"]),padding=16,margin=ft.margin.only(bottom=12),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text("Riwayat Kehadiran", size=15,weight=ft.FontWeight.W_700, color=C["text"]),
                        bgcolor=C["surface"],
                        border=ft.border.only(bottom=ft.BorderSide(1, C["border"])),
                        padding=ft.padding.symmetric(horizontal=16, vertical=13),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=4),
                                rekap_card,
                                log_card,
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
