# views/login.py

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

        user = proses_login(username, password)
        
        if not user:
            self.err_ref.current.value = "NIS/NIP atau password salah!"
            self.err_ref.current.visible = True
            self.page.update()
            return
        
        self.state["user_role"] = user["role"]
        self.state["user_data"] = user
        self.state["user_id"] = user["id_siswa"]
        
        self.page.session.set("user_id", user["id_siswa"])
        self.page.session.set("user_nama", user["nama"])

        self.err_ref.current.visible = False
        self.go_to(f"/{user['role']}", tab=0)

    def set_demo(self, role: str):
        self.ref_user.current.value = "12345" if role == "siswa" else "admin123"
        self.ref_pass.current.value = "sjakhyakirti2026" if role == "siswa" else "foradminsjakhyakirti2026"
        self.page.update()

    def build(self) -> ft.View:
        return ft.View(
            route="/login", bgcolor="#FFFFFF", padding=0,
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
                    bgcolor="#FFFFFF",
                    content=ft.ListView( 
                        expand=True,
                        padding=ft.padding.symmetric(horizontal=28, vertical=40),
                        controls=[
                            
                            # 2. Kotak Biru (Logo + Teks Sistem)
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Image(src="/logo_kirti_fix.png", width=80, height=80,  fit=ft.ImageFit.CONTAIN),
                                        ft.Text(
                                            "SISTEM ABSENSI DIGITAL", size=20, weight=ft.FontWeight.W_900,color="#FFFFFF", text_align=ft.TextAlign.CENTER),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=10,
                                ),
                                width=300, padding=ft.padding.all(30), border_radius=15,bgcolor="#1A4BD4", alignment=ft.alignment.center, margin=ft.margin.only(bottom=20),
                            ),

                            # 3. Teks Sekolah
                            ft.Text("SMA SJAKHYAKIRTI", size=22, weight=ft.FontWeight.W_800,color=C["text"], text_align=ft.TextAlign.CENTER),
                            
                            # 4. Teks Kota
                            ft.Container(
                                content=ft.Text("Palembang",size=13,color=C["text2"],text_align=ft.TextAlign.CENTER),
                                margin=ft.margin.only(bottom=36),
                            ),

                            # 5. Form Login
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        field_input("NISN / NIP", hint="Masukkan NISN atau NIP",ref=self.ref_user),
                                        ft.Container(height=10),
                                        field_input("Password",hint="••••••••",password=True,ref=self.ref_pass),
                                        ft.Container(height=6),
                                        ft.Text("",ref=self.err_ref,color=C["red"],size=12,visible=False),
                                        ft.Container(height=10),
                                        ft.Container(
                                            content=ft.Text("Masuk",size=15,weight=ft.FontWeight.W_800,color="#FFFFFF",text_align=ft.TextAlign.CENTER),
                                            bgcolor="#1A4BD4",border_radius=10,padding=ft.padding.symmetric(vertical=14),on_click=self.do_login, ink=True),
                                        ft.Container(height=16),
                                        ft.Row(
                                            controls=[
                                                ft.Text("Demo: ", size=12, color=C["text3"]),ft.TextButton("Siswa", on_click=lambda e:self.set_demo("siswa")),
                                                ft.Text("·", size=12, color=C["text3"]), ft.TextButton("Admin", on_click=lambda e: self.set_demo("admin")),
                                            ],
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            spacing=4,
                                        ),
                                    ],
                                ),
                                bgcolor=C["surface"],border_radius=20,border=ft.border.all(1, C["border2"]),padding=28,shadow=ft.BoxShadow(blur_radius=40,color="#00000015"),
                            ),
                        ],
                    ),
                ),
            ],
        )