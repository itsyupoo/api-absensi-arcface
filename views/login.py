import flet as ft
from components.ui import C, field_input, primary_button
from database_connect import proses_login

class LoginView:
    def __init__(self, page: ft.Page, state: dict, go_to):
        self.page   = page
        self.state  = state
        self.go_to  = go_to
        self.ref_user = ft.Ref[ft.TextField]()
        self.ref_pass = ft.Ref[ft.TextField]()
        self.err_ref  = ft.Ref[ft.Text]()

    def do_login(self, e):
        username = self.ref_user.current.value.strip()
        password = self.ref_pass.current.value.strip()

        if not username or not password:
            self.err_ref.current.value = "Harap isi NISN/NIP dan Password!"
            self.err_ref.current.visible = True
            self.page.update()
            return
        self.err_ref.current.value = "Sedang memverifikasi..."
        self.err_ref.current.color = "blue"
        self.err_ref.current.visible = True
        self.page.update()

        hasil = proses_login(username, password)

        if hasil["status"] == "success":
            role = hasil["data"].get("role")
            self.state["user_data"] = hasil["data"] 
            self.state["user_role"] = hasil["data"].get("role")
            
            if role == "admin":
                self.go_to("/admin")
            else:
                self.go_to("/siswa")
        else:
            # Jika gagal, tampilkan pesan error dari database
            self.err_ref.current.value = hasil["message"]
            self.err_ref.current.color = "red"
            self.err_ref.current.visible = True
            self.page.update()

      
        
    def build(self) -> ft.View:
        return ft.View(
            route="/login", 
            bgcolor="#FFFFFF", 
            padding=0,
            # PENTING: Gunakan vertical_alignment dan horizontal_alignment di View
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    expand=True,
                    bgcolor="#FFFFFF",
                    # Kita buat Container ini mengisi seluruh View
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            # Wrapper agar konten tetap di tengah
                            ft.Container(
                                content=ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=10,
                                    controls=[
                                        # 1. Kotak Biru
                                        ft.Container(
                                            content=ft.Column(
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                spacing=10,
                                                controls=[
                                                    ft.Image(src="/logo_kirti_fix.png", width=80, height=80, fit="contain"),
                                                    ft.Text("SISTEM ABSENSI DIGITAL", size=20, weight="bold", color="#FFFFFF", text_align="center"),
                                                ],
                                            ),
                                            expand=True,
                                            margin=ft.Margin(0, 0, 0, 20), 
                                            padding=30, border_radius=15, 
                                            bgcolor="#1A4BD4", 
                                        ),
                                        # 2. Form Login
                                        ft.Container(
                                            content=ft.Column(
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                controls=[
                                                    field_input("NISN / NIP", hint="Masukkan NISN atau NIP", ref=self.ref_user),
                                                    ft.Container(height=10),
                                                    field_input("Password", hint="••••••••", password=True, ref=self.ref_pass),
                                                    ft.Text("", ref=self.err_ref, color="red", size=12, visible=False),
                                                    ft.Container(height=10),
                                                    ft.ElevatedButton(
                                                        "Masuk",
                                                        on_click=self.do_login,
                                                        width=300, height=50,
                                                        style=ft.ButtonStyle(bgcolor="#1A4BD4", color="#FFFFFF"),
                                                    ),
                                                ],
                                            ),
                                            bgcolor="#FFFFFF", border_radius=20,
                                            border=ft.Border(
                                                left=ft.BorderSide(1, "#D1D1D1"), top=ft.BorderSide(1, "#D1D1D1"),
                                                right=ft.BorderSide(1, "#D1D1D1"), bottom=ft.BorderSide(1, "#D1D1D1"),
                                            ),
                                            padding=28, width=350,
                                        ),
                                    ]
                                )
                            )
                        ]
                    )
                )
            ]
        )