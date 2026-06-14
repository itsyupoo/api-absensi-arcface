# views/siswa/profil.py

import flet as ft
from components.ui import C, chip, avatar, info_row

class SiswaProfil:
    def __init__(self, page, state, go_to):
        self.page  = page
        self.state = state
        self.go_to = go_to

    def handle_logout(self, e):
        self.state["user_data"] = {}
        self.go_to("/login")

    def build(self) -> ft.Container:
        user = self.state.get("user_data", {})
        nama = user.get("nama", "Siswa")
        nis = user.get("NIS", "-")
        kelas = user.get("kelas", "-")
        jenis_kelamin = user.get("jenis_kelamin", "-")
        wa_ortu = user.get("wa_ortu", "-")
        role = user.get("role", "siswa")

        jk_lower = str(jenis_kelamin).lower()
        if jk_lower in ["p", "perempuan", "cewek"]:
            avatar_path = "avatar_cewek.png"
        else:
            avatar_path = "avatar_cowok.png"
        
        status_wa = "✓ Aktif" if wa_ortu and wa_ortu != "-" else "✕ Belum Terdaftar"

        profil_data = [
            ("Nama Lengkap", nama),
            ("NIS",           nis),
            ("Kelas",         kelas),
            ("Jenis Kelamin", jenis_kelamin),
            ("No. WA Orang Tua", wa_ortu),
            ("Notif WA",    status_wa),
        ]

        def card_section(title, rows_data, extra_colors=None):
            rows = []
            for i, (k, v) in enumerate(rows_data):
                color = None
                if extra_colors and v in extra_colors:
                    color = extra_colors[v]
                rows.append(info_row(k, v, value_color=color))
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(title, size=14, weight=ft.FontWeight.W_700,
                                color=C["text"]),
                        ft.Container(height=8),
                        *rows,
                    ],
                    spacing=0,
                ),
                bgcolor=C["surface"],
                border_radius=12,
                border=ft.border.all(1, C["border"]),
                padding=16,
                margin=ft.Margin(bottom=12, left=0, right=0, top=0),
            )

        return ft.Container(
            bgcolor=C["bg"],
            expand=True,
            content=ft.Column(
                spacing=0,
                controls=[
                    # 1. Header: Kita beri padding atas lebih besar (top=50)
                    ft.Container(
                        bgcolor="#0D47A1",
                        border=ft.Border(bottom=ft.BorderSide(1, C["border"])),
                        padding=ft.Padding(left=20, right=16, top=50, bottom=20),
                        width=float("inf"),
                        content=ft.Text("PROFIL SAYA", size=35, weight=ft.FontWeight.W_900, color="white", text_align=ft.TextAlign.CENTER,),
                    ),
                    # 2. Konten Profil: Kita beri padding atas (top=20) agar kotak turun
                    ft.Container(
                        padding=ft.Padding(left=16, right=16, top=20, bottom=16),
                        content=ft.Column(
                            spacing=12,
                            scroll=ft.ScrollMode.AUTO,
                            controls=[
                                # Hero Profil
                                ft.Container(
                                    content=ft.Column(
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=8,
                                        controls=[
                                            ft.Image(src=avatar_path, width=76, height=76, fit="contain"),
                                            ft.Text(nama, size=20, weight=ft.FontWeight.W_800, color=C["text"], text_align=ft.TextAlign.CENTER),
                                            ft.Text(f"{kelas} · SMA Sjakhyakirti Palembang", size=12, color=C["text2"], text_align=ft.TextAlign.CENTER),
                                            ft.Row(
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                spacing=8,
                                                controls=[chip(f"NIS: {nis}", "blue"), chip(role.upper(), "green")]
                                            ),
                                        ],
                                    ),
                                    bgcolor=C["surface"],
                                    border_radius=12,
                                    border=ft.border.all(1, C["border"]),
                                    padding=24,
                                ),
                                # Informasi Akun
                                card_section("📱 Informasi Akun", profil_data, 
                                             extra_colors={"✓ Aktif": C["green"], "✕ Belum Terdaftar": C["red"]}),
                                # Tombol Logout
                                ft.Container(
                                    content=ft.Text("Keluar / Logout", size=14, weight=ft.FontWeight.W_700, color="#FFFFFF", text_align=ft.TextAlign.CENTER),
                                    bgcolor="#0D47A1",
                                    border_radius=12,
                                    padding=13,
                                    on_click=self.handle_logout,
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )