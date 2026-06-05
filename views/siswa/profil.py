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
        role = user.get ("role", "siswa")

        jk_lower = str(jenis_kelamin).lower()
        if jk_lower in ["p", "perempuan", "cewek"]:
            avatar_path = "avatar_cewek.png"
        else:
            # Default ke cowok jika Laki-laki atau data tidak terisi dengan benar
            avatar_path = "avatar_cowok.png"

        status_wa = "✓ Aktif" if wa_ortu and wa_ortu != "-" else "✕ Belum Terdaftar"

        profil_data = [
            ("Nama Lengkap", nama),
            ("NIS",          nis),
            ("Kelas",        kelas),
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
                margin=ft.margin.only(bottom=12),
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text("Profil Saya", size=15,
                                        weight=ft.FontWeight.W_700, color=C["text"]),
                        bgcolor=C["surface"],
                        border=ft.border.only(
                            bottom=ft.BorderSide(1, C["border"])
                        ),
                        padding=ft.padding.symmetric(horizontal=16, vertical=13),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=4),

                                # Hero profil
                                ft.Container(
                                    content=ft.Column(
                                        controls=[
                                           ft.Container(
                                                content=ft.Image(
                                                    src=avatar_path,
                                                    width=76,
                                                    height=76,
                                                    fit=ft.ImageFit.CONTAIN,
                                                ),
                                                shape=ft.BoxShape.CIRCLE,
                                                alignment=ft.alignment.center,
                                            ),
                                            ft.Text(nama, size=20,
                                                    weight=ft.FontWeight.W_800,
                                                    color=C["text"],
                                                    text_align=ft.TextAlign.CENTER),
                                            ft.Text(f"{kelas} · SMA Sjakhyakirti Palembang",
                                                    size=12, color=C["text2"],
                                                    text_align=ft.TextAlign.CENTER),
                                            ft.Row(
                                                controls=[
                                                    chip(f"NIS: {nis}", "blue"),
                                                    chip(role.upper(), "green"),
                                                ],
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                spacing=8,
                                            ),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=8,
                                    ),
                                    bgcolor=C["surface"],
                                    border_radius=12,
                                    border=ft.border.all(1, C["border"]),
                                    padding=ft.padding.symmetric(
                                        horizontal=16, vertical=24
                                    ),
                                    margin=ft.margin.only(bottom=12),
                                ),

                                card_section("📱 Informasi Akun", profil_data,
                                    extra_colors={
                                        "✓ Aktif": C["green"],
                                        "✕ Belum Terdaftar": C["red"]
                                    },    
                                ),

                                # Logout button
                                ft.Container(
                                    content=ft.Text(
                                        "Keluar / Logout",
                                        size=14, weight=ft.FontWeight.W_700,
                                        color="#FFFFFF",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    bgcolor="#0D47A1",
                                    border_radius=12,
                                    border=ft.border.all(1, f"{C['red']}40"),
                                    padding=ft.padding.symmetric(vertical=13),
                                    on_click=self.handle_logout,
                                    ink=True,
                                    margin=ft.margin.only(bottom=24),
                                ),
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
