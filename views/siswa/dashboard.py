# views/siswa/dashboard.py

import flet as ft
from components.ui import C, card, stat_box, avatar, chip, section_title, divider
import datetime
from database_connect import ambil_statistik_siswa, cek_presensi_hari_ini, ambil_notifikasi_siswa, ambil_statistik_siswa_by_id

class SiswaDashboard:
    def __init__(self, page, state, go_to):
        self.page   = page
        self.state  = state
        self.go_to  = go_to

    def mulai_presensi(self, e):
        id_siswa = self.state["user_data"]["id_siswa"]
        nama = self.state["user_data"]["nama"]
        url = (
            "https://sjakhyakirtibackendapi-production.up.railway.app/"
            f"presensi-web?id_siswa={id_siswa}&nama={nama}"
        )

        self.page.launch_url(url)

    def build(self) -> ft.Container:
        if self.state.get("dashboard_refresh"):
            print("REFRESH DASHBOARD")
            self.state["dashboard_refresh"] = False
            
        user = self.state.get("user_data", {})
        if not user:
            return ft.Container(content=ft.Text("Data tidak ditemukan!"), padding=20)
        id_siswa = user.get("id_siswa", 0)

        # 1. Ambil data Real-time (Hapus baris yang self.state.get("sudah_hadir"))
        sudah_hadir = cek_presensi_hari_ini(id_siswa)
        res_stats = ambil_statistik_siswa(id_siswa) or {"hadir": 0, "terlambat": 0, "persen": "0%"}
        data_notif_db = ambil_notifikasi_siswa(id_siswa) or []

        # 2. Ambil Profil (Pastikan 'nama', 'kelas', 'nis' sesuai nama kolom di DB)
        nama  = user.get("nama", "Data tidak ditemukan")
        kelas = user.get("kelas", "kelas") 
        nis   = user.get("NIS", "NIS") 
        jenis_kelamin    = user.get("jenis_kelamin", "Laki-laki")

        if jenis_kelamin.lower() == "perempuan":
             siswa_avatar = ft.Image(src="avatar_cewek.png",width=37,height=37,fit="contain")
        else:
             siswa_avatar = ft.Image(src="avatar_cowok.png", width=37,height=37,fit="contain")

        # 3. Proses Notifikasi (Perbaiki Indentasi)
        notifs = []
        for icon, pesan, is_baru in data_notif_db:
            notifs.append((icon, pesan, is_baru))

        # ── Hero Card ──
        hero = ft.Container(
            content=ft.Column(
                controls=[
                    # Baris Status Absen
                    ft.Row(
                        [
                            ft.Container(expand=True), 
                            chip("✓ Sudah Hadir" if sudah_hadir else "● Belum Absen", 
                                 color="green" if sudah_hadir else "red")
                        ], 
                        alignment=ft.MainAxisAlignment.END
                    ),
                    
                    # Baris Konten Utama (Gambar + Teks)
                    ft.Row(
                        controls=[
                            ft.Image(src="intro.png", width=130, height=130, fit="contain"),
                            ft.Column(
                                controls=[
                                    ft.Text("Selamat Datang 👋", size=12, color="#FFFFFF", weight="bold"),
                                    ft.Text(nama, size=18, weight="bold", color="#FFFFFF"),
                                    ft.Text(f"NIS: {nis} · {kelas}", size=12, color="#FFFFFF"),
                                ],
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER,
                                expand=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=5, # Jarak kecil antara status chip dan konten utama
            ),
            bgcolor="#1A4BD4",
            padding=16,
            border_radius=15,
        )
        # ── Tombol Presensi ──
        btn_presensi = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CAMERA_ALT_ROUNDED, color="#FFFFFF", size=22),
                    ft.Text(
                        "✅ Sudah Presensi" if sudah_hadir else "Mulai Presensi Sekarang",
                        size=16, weight=ft.FontWeight.W_800,
                        color="#FFFFFF" if not sudah_hadir else C["text2"],
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            bgcolor="#1A4BD4" if not sudah_hadir else C["surface3"],
            border_radius=12,
            padding=ft.Padding(left=0, top=16, right=0, bottom=16),
            on_click=self.mulai_presensi if not sudah_hadir else None,
            ink=not sudah_hadir, 
            margin=ft.Margin(0, 0, 0, 0),
            shadow=ft.BoxShadow(
                blur_radius=20, color="#4F8EF740", offset=ft.Offset(0, 6)
            ) if not sudah_hadir else None,
        )
        # ── Rekap Kehadiran Horizontal ──
        try:
            id_siswa = self.state["user_data"].get("id_siswa", 0)
            res_stats = ambil_statistik_siswa_by_id(id_siswa)
            if not res_stats:
                res_stats = {"hadir": 0, "terlambat": 0, "persen": "0%"}
        except Exception as e:
            res_stats = {"hadir": 0, "terlambat": 0, "persen": "0%"}
        
        # ── Rekap Kehadiran (Uji Coba Paling Sederhana) ──
        rekap_horizontal = ft.Container(
            content=ft.Row(
                controls=[
                    # Kotak Hadir
                    ft.Container(
                        expand=True,
                        content=ft.Column([
                            ft.Text("Hadir", size=12, color="white"),
                            ft.Text(str(res_stats.get("hadir", 0)), size=24, weight="bold", color="white"),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        width=130, padding=15, bgcolor="green", border=ft.border.all(1, ft.Colors.GREEN_800), border_radius=15
                    ),
                    # Kotak Terlambat
                    ft.Container(
                        expand=True,
                        content=ft.Column([
                            ft.Text("Terlambat", size=12, color="white"),
                            ft.Text(str(res_stats.get("terlambat", 0)), size=24, weight="bold", color="white"),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        width=130, padding=15, bgcolor="red", border=ft.border.all(1, ft.Colors.RED_800), border_radius=15
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            margin=ft.Margin(0,0,0,10),
        )
        # ── Notifikasi ──
        notif_items = []
        for ico, teks, baru in notifs:
            notif_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(ico, size=16),
                            ft.Text(teks, size=12, color=C["text2"], expand=True),
                            chip("Baru", "blue") if baru else ft.Container(),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    border=ft.Border(bottom=ft.BorderSide(1, C["border"])
                    ),
                    padding=ft.Padding(left=0, top=8, right=0, bottom=8),
                )
            )

        notif_card = card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            section_title("🔔 Notifikasi"),chip("2 Baru", "blue")],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=8),*notif_items,
                ],
                spacing=0,
            )
        )
           
        # ── Return Final (Revisi Padding agar tidak error) ──
        return ft.Container(
            expand=True,
            bgcolor=C["bg"],
            content=ft.SafeArea(
                ft.Column(
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        # 1. Topbar (Header)
                        ft.Container(
                            bgcolor=C["surface"],
                            border=ft.Border(bottom=ft.BorderSide(1, C["border"])),
                            padding=16,
                            content=ft.Row([
                                ft.Column([
                                    ft.Text("SMA Sjakhyakirti", size=16, weight="bold", color=C["blue"]),
                                    ft.Text("Dashboard Siswa", size=13, color=C["text2"])
                                ], spacing=0, expand=True),
                                siswa_avatar
                            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ),
                        
                        # 2. Konten Utama
                        ft.Container(
                            expand=True,
                            padding=16,
                            content=ft.Column(
                                scroll=ft.ScrollMode.AUTO,
                                spacing=15,
                                controls=[hero, btn_presensi, rekap_horizontal, notif_card],
                            ),
                        ),
                    ],
                )
            ),
        )