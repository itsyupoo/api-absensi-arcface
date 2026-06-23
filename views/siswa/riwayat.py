# views/siswa/riwayat.py

import flet as ft
from components.ui import C, chip, stat_box
from database_connect import get_db_connection, ambil_statistik_siswa
from datetime import datetime

class SiswaRiwayat:
    def __init__(self, page, state, go_to):
        self.page  = page
        self.state = state
        self.go_to = go_to

        self.box_hadir = ft.Container("0", "Hadir", "blue")
        self.box_telat = ft.Container("0", "Terlambat", "warn")
        self.box_alfa  = ft.Container("0", "Alfa", "red")
        self.box_persen = ft.Container("0%", "Tingkat", "green")
        
    def get_indonesia_day(self, date_obj):
        days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        return days[date_obj.weekday()]
    
    def get_indonesia_month(self, date_obj):
        months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"]
        return months[date_obj.month - 1]
    
    def fetch_riwayat_data(self):
        user_data = self.state.get("user_data", {})
        user_id = user_data.get("id_siswa")
        data = {"stats": {"hadir": 0, "terlambat": 0, "persen": "0%"}, "logs": []}
        if not user_id: return data
        data["stats"] = ambil_statistik_siswa(user_id) or data["stats"]
        db = get_db_connection()
        if db:
            try:
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT status_kehadiran, waktu_absen FROM catatan_kehadiran WHERE id_siswa = %s ORDER BY waktu_absen DESC", (user_id,))
                data["logs"] = cursor.fetchall()
            except Exception as e: print(f"Error DB: {e}")
            finally: db.close()
        return data
    
    def build(self) -> ft.Container:
        data = self.fetch_riwayat_data()
        stats = data["stats"]
        logs = data["logs"]

        # Definisi rekap_card (Gunakan ini untuk menggantikan yang lama)
        rekap_card = ft.Container(
            bgcolor=C["surface"],
            border_radius=12,
            border=ft.Border(left=ft.BorderSide(1, C["border"]), top=ft.BorderSide(1, C["border"]), right=ft.BorderSide(1, C["border"]), bottom=ft.BorderSide(1, C["border"])),
            padding=ft.Padding(top=16, bottom=16, left=8, right=8),
            width=float("inf"),
            content=ft.Column([
                # Header Rekap
                ft.Row([
                    ft.Text(f"📊 Rekap {datetime.now().strftime('%B %Y')}", size=14, weight="bold", color=C["text"]),
                    chip("Aktif", "green"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=16),
                
                # Baris Statistik (Warna dan Bolding Disesuaikan)
                ft.Row([
                    # Hadir (Hijau)
                    ft.Column([
                        ft.Text(str(stats.get("hadir", 0)), weight="bold", size=16, color="green"),
                        ft.Text("HADIR", size=14, weight="bold", color="green")
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    
                    # Terlambat (Merah)
                    ft.Column([
                        ft.Text(str(stats.get("terlambat", 0)), weight="bold", size=16, color="red"),
                        ft.Text("TERLAMBAT", size=14, weight="bold", color="red")
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    
                    # Tingkat (Orange) - Alfa dihapus
                    ft.Column([
                        ft.Text(stats.get("persen", "0%"), weight="bold", size=16, color="orange"),
                        ft.Text("TINGKAT", size=14, weight="bold", color="orange")
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY) # Membagi ruang rata
            ], spacing=0)
        )

       # Ganti bagian loop log_controls ini:
        log_controls = []
        for row in logs:
            dt = row['waktu_absen']
            status = row['status_kehadiran']
            log_controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Text(f"{dt.day} {self.get_indonesia_month(dt)}", color=C["text"], size=14),
                            ft.Container(width=10),
                            ft.Text(status, color="black", weight="bold", size=14),
                        ]), 
                        ft.Text(dt.strftime("%H:%M"), color="blue", size=14)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN, 
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=10,
                    border=ft.Border(bottom=ft.border.BorderSide(1, C["border"]))
                )
            )
       
        # Main return
        return ft.Container(
            expand=True,
            bgcolor=C["bg"],
            content=ft.SafeArea(
                ft.Column(
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        # 1. Header yang sudah disamakan polanya
                        ft.Container(
                            bgcolor=C["surface"],
                            border=ft.Border(bottom=ft.BorderSide(1, C["border"])),
                            padding=16,
                            content=ft.Text(
                                "Riwayat Kehadiran",
                                size=18,
                                weight=ft.FontWeight.W_700,
                                color=C["text"]
                            ),
                        ),
                    # 2. Body (Scrollable)
                    ft.Container(
                        padding=16,
                        content=ft.Column(
                            scroll=ft.ScrollMode.AUTO,
                            spacing=10,
                            controls=[
                                rekap_card, 
                                ft.Container(
                                    bgcolor=C["surface"],
                                    border_radius=12,
                                    border=ft.Border(left=ft.BorderSide(1, C["border"]), top=ft.BorderSide(1, C["border"]), right=ft.BorderSide(1, C["border"]), bottom=ft.BorderSide(1, C["border"])),
                                    padding=16,
                                    content=ft.Column([
                                        ft.Text("📋 Log Harian", size=14, weight=ft.FontWeight.W_700, color=C["text"]),
                                        *log_controls # Semua log muncul di sini
                                    ])
                            )
                        ]
                    )
                )
            ]
        )
    )
)