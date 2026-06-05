# views/siswa/dashboard.py

import flet as ft
from components.ui import C, card, stat_box, avatar, chip, section_title, divider
import datetime
from database_connect import ambil_statistik_siswa, cek_presensi_hari_ini, ambil_notifikasi_siswa

class SiswaDashboard:
    def __init__(self, page, state, go_to):
        self.page   = page
        self.state  = state
        self.go_to  = go_to

    def build(self) -> ft.Container:
        user = self.state.get("user_data", {})
        id_siswa = user.get("id_siswa")

        # 1. Ambil data Real-time (Hapus baris yang self.state.get("sudah_hadir"))
        sudah_hadir = cek_presensi_hari_ini(id_siswa)
        res_stats = ambil_statistik_siswa(id_siswa)
        data_notif_db = ambil_notifikasi_siswa(id_siswa)

        # 2. Ambil Profil (Pastikan 'nama', 'kelas', 'nis' sesuai nama kolom di DB)
        nama  = user.get("nama", "Data tidak ditemukan")
        kelas = user.get("kelas", "kelas") 
        nis   = user.get("NIS", "NIS") 
        jenis_kelamin    = user.get("jenis_kelamin", "Laki-laki")

        if jenis_kelamin.lower() == "perempuan":
             siswa_avatar = ft.Image(src="avatar_cewek.png",width=34,height=34,fit=ft.ImageFit.CONTAIN)
        else:
             siswa_avatar = ft.Image(src="avatar_cowok.png", width=34,height=34,fit=ft.ImageFit.CONTAIN)

        # 3. Proses Notifikasi (Perbaiki Indentasi)
        notifs = []
        for icon, pesan, is_baru in data_notif_db:
            notifs.append((icon, pesan, is_baru))

        # ── Hero Card ──
        hero = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                              content=ft.Image(src="intro.png",width=90,height=90,fit=ft.ImageFit.CONTAIN),
                              padding=5,
                              margin=ft.margin.only(right=10),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("Selamat Datang 👋", size=11,color="#FFFFFF",weight=ft.FontWeight.W_700),
                                    ft.Text(nama, size=20,weight=ft.FontWeight.W_800,color="#FFFFFF"),
                                    ft.Text(f"NIS: {nis} · {kelas}",size=12, color=C["text2"]),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                            chip(
                                "✓ Sudah Hadir" if sudah_hadir else "● Belum Absen",color="green" if sudah_hadir else "red",
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Container(height=16),
                    ft.Row(
                        controls=[
                            stat_box(str(res_stats["hadir"]), "Hadir", "warn"),
                            stat_box(str(res_stats["terlambat"]), "Terlambat", "red"),
                            stat_box(res_stats["persen"], "Kehadiran", "green"),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=0,
            ),
            bgcolor="#1A4BD4",
            border_radius=16,
            border=ft.border.all(1, "#1A4BD4"),padding=20,
            margin=ft.margin.only(bottom=12),
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
            padding=ft.padding.symmetric(vertical=16),
            on_click=(lambda e: self.go_to("/siswa", tab=1)) if not sudah_hadir else None,
            ink=not sudah_hadir,
            margin=ft.margin.only(bottom=12),
            shadow=ft.BoxShadow(
                blur_radius=20, color="#4F8EF740", offset=ft.Offset(0, 6)
            ) if not sudah_hadir else None,
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
                    border=ft.border.only(bottom=ft.BorderSide(1, C["border"])
                    ),
                    padding=ft.padding.symmetric(vertical=8),
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

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Topbar
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text("SMA Sjakhyakirti", size=13,weight=ft.FontWeight.W_700,color=C["blue"]),
                                        ft.Text("Dashboard Siswa", size=11,color=C["text2"]),
                                    ],
                                    spacing=1,
                                    expand=True,
                                ),
                                siswa_avatar,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=C["surface"],
                        border=ft.border.only(
                            bottom=ft.BorderSide(1, C["border"])
                        ),
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    ),

                    # Scrollable body
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=4),hero,btn_presensi,notif_card,
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
