# views/admin/data siswa.py

import flet as ft
from components.ui import C, chip, section_title
from database_connect import simpan_siswa, ambil_semua_wajah
import json
import threading
import time
import requests
import traceback

class AdminDataSiswa:
    def __init__(self, page, state, go_to):
        self.page  = page
        self.state = state
        self.go_to = go_to
        self.photo_slots = [False, False, False, False, False]
        self.photo_refs  = [ft.Ref[ft.Container]() for _ in range(5)]
        self.ref_nama = ft.Ref[ft.TextField]()
        self.ref_nis  = ft.Ref[ft.TextField]()
        self.ref_wa   = ft.Ref[ft.TextField]() 
        self.ref_kelas = ft.Ref[ft.Dropdown]()
        self.ref_jk = ft.Ref[ft.Dropdown]()
        self.list_siswa_controls = []
        self.count_text_ref = ft.Ref[ft.Text]()
        self.timer = None
        self.all_data = ambil_semua_wajah()
        self.status_text = ft.Text("Belum ada foto", size=11, color="grey")
        self.status_icon = ft.Icon("info_outline", size=20, color="grey")
        self.fp = ft.FilePicker()
        self.page.services.append(self.fp)

    def _snack(self, msg, color="green"):
        snack = ft.SnackBar(
            content=ft.Text(
                msg,
                color="white",
                weight=ft.FontWeight.BOLD
            ),
            bgcolor=color,
            behavior=ft.SnackBarBehavior.FLOATING,
            duration=3000
        )

        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def refresh_data(self):
        data_db = ambil_semua_wajah()
        new_rows = []
        for s in data_db:
            jk = s.get('jenis_kelamin', 'Laki-laki')
            path_logo = "/logo_cowok.png" if jk == "Laki-laki" else "/logo_cewek.png"
            row = self.siswa_row(path_logo, s.get('nama', 'Tanpa Nama'), s.get('nis', '-'), s.get('kelas', 'Kelas ?'), s.get('wa_ortu', '-'))
            new_rows.append(row)
        self.list_siswa_controls.clear()
        self.list_siswa_controls.extend(new_rows)
            
    def siswa_row(self, path_logo, nama, nis, kelas, wa):
        return ft.Container(
            height=70, 
            padding=ft.Padding(left=10,right=10, top=5, bottom=5),
            bgcolor="white",
            border=ft.border.all(1, "#E0E0E0"),
            border_radius=8,
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=40, height=40,
                        border_radius=20,
                        bgcolor="#F0F0F0",
                        content=ft.Image(
                            src=path_logo, 
                            width=40, height=40, 
                            fit="cover",
                            error_content=ft.Icon(ft.Icons.PERSON, color="grey"),
                        ),
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    ),
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(nama, size=14, weight=ft.FontWeight.BOLD, color="black"),
                            ft.Text(f"NIS: {nis} | {kelas}", size=12, color="#616161"),
                        ], 
                    ),
                ],
            ),
        )

    def filter_pencarian(self, e):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(0.3, self.jalankan_filter, args=[e.control.value])
        self.timer.start()

    def jalankan_filter(self, query):
        query = query.lower()
        filtered_rows = []
        for s in self.all_data:
            nama = s.get('nama', '').lower()
            if query in nama:
                jk = s.get('jenis_kelamin', 'Laki-laki')
                path_logo = "/logo_cowok.png" if jk == "Laki-laki" else "/logo_cewek.png"
                filtered_rows.append(self.siswa_row(path_logo, s.get('nama'), s.get('nis'), s.get('kelas'), s.get('wa_ortu')))
        self.list_siswa_controls.clear()
        self.list_siswa_controls.extend(filtered_rows)

    async def pilih_foto(self, e):
        print("Tombol pilih foto ditekan")
        files = await self.fp.pick_files(
            allow_multiple=True,
            file_type=ft.FilePickerFileType.IMAGE
        )
        print("files")
        if not files:
            self._snack("❌ Tidak ada foto dipilih", color="red")
            return
        if "selected_images" not in self.state:
            self.state["selected_images"] = []
        for f in files:
            print("PATH =", f.path)
            print("NAME =", f.name)
            self._snack(
                f"PATH={f.path}",
                color="blue"
            )
            self.state["selected_images"].append(f.path)
        jumlah_baru = len(files)
        jumlah_total = len(self.state["selected_images"])
        self._snack(
           f"✅ {jumlah_baru} foto ditambahkan (total {jumlah_total} foto)",
            color="green"
        )
        # Update indikator slot
        for i in range(5):
            if i < len(files):
                self.photo_slots[i] = True

                if self.photo_refs[i].current:
                    self.photo_refs[i].current.content = ft.Text("✅", size=20)
                    self.photo_refs[i].current.bgcolor = "green"

            else:
                self.photo_slots[i] = False

                if self.photo_refs[i].current:
                    self.photo_refs[i].current.content = ft.Text("📷", size=20)
                    self.photo_refs[i].current.bgcolor = C["surface2"]
        self.page.update()
            
    def proses_simpan(self, e):
        nama = self.ref_nama.current.value
        nis = self.ref_nis.current.value
        kelas = self.ref_kelas.current.value
        wa = self.ref_wa.current.value
        jk = self.ref_jk.current.value

        images = self.state.get("selected_images", [])

        # Validasi input
        if not nama or not nis:
            self._snack(
                "⚠️ Nama dan NISN wajib diisi!",
                color="orange"
            )
            return

        if len(images) < 5:
            self._snack(
                "⚠️ Minimal 5 foto diperlukan!",
                color="orange"
            )
            return

        e.control.disabled = True
        self.page.update()

        try:
            self._snack(
                "⏳ Mengirim foto ke server AI...",
                color="blue"
            )

            files = []

            self._snack(
                f"DEBUG IMAGES = {images}",
                color="blue"
            )
            print("IMAGES =", images)
            for path in images:

                print("PATH =", path)
                print("TYPE =", type(path))

                if path is None:

                    self._snack(
                        "PATH FOTO = NONE",
                        color="red"
                    )

                    return

                files.append(
                    (
                        "files",
                        (
                            path.split("\\")[-1],
                            open(path, "rb"),
                            "image/jpeg"
                        )
                    )
                )

            data = {
                "nis_siswa": nis,
                "nama_siswa": nama,
                "kelas_siswa": kelas,
                "jenis_kelamin": jk,
                "wa_ortu": wa
            }
            print("=== MENGIRIM DATA KE RAILWAY ===")
            print(data)
            print(images)
            response = requests.post(
                "https://sjakhyakirtibackendapi-production.up.railway.app/admin/input-siswa",
                data=data,
                files=files,
                timeout=300
            )
            print("Status code =", response.status_code)
            print("Response text =", response.text)

            hasil = response.json()

            if response.status_code == 200 and hasil["status"] == "sukses":

                self._snack(
                    f"✅ {nama} berhasil disimpan ke Database Railway!",
                    color="green"
                )

                # Reset form
                self.ref_nama.current.value = ""
                self.ref_nis.current.value = ""
                self.ref_wa.current.value = ""
                self.ref_kelas.current.value = None
                self.ref_jk.current.value = None
                self.state["selected_images"] = []

                self.refresh_data()

            else:
                self._snack(
                    hasil["message"],
                    color="red"
                )

        except Exception as err:

            print("========== ERROR ==========")
            traceback.print_exc()

            self._snack(
                f"❌ {str(err)}",
                color="red"
            )

        finally:

            # menutup file
            for _, file_info in files:
                file_info[1].close()

            e.control.disabled = False
            self.page.update()

    def get_opsi_kelas(self):
        opsi = []
        for jenjang in ['X', 'XI', 'XII']:
            for sub in range(1, 8):
                opsi.append(ft.dropdown.Option(text=f"{jenjang}.{sub}", content=ft.Text(f"{jenjang}.{sub}", color="black", weight="bold")))
        return opsi
    
    def build(self) -> ft.Container:
        self.refresh_data()

        list_card = ft.Container(
            bgcolor=C["surface"],
            border_radius=12,
            border=ft.border.all(1, C["border"]),
            padding=16,
            margin=ft.Margin(bottom=12),
            content=ft.Column(
                tight=True,
                controls=[
                    ft.Container(
                        content=ft.TextField(
                            hint_text="Cari berdasarkan nama, NIS, atau kelas...",
                            prefix_icon=ft.Icons.SEARCH,
                            on_change=self.filter_pencarian,
                            border_radius=8,
                            height=50,
                            bgcolor="white",
                            text_style=ft.TextStyle(color="black", size=14),
                            border_color="black",
                            focused_border_color="black",
                            border_width=1.5,
                        ),
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            section_title("👥 Daftar Siswa"),
                            ft.Container(
                                content=ft.Text(f"{len(self.list_siswa_controls)} Siswa", ref=self.count_text_ref, size=11, color="white", weight="bold"),
                                bgcolor="blue", padding=5, border_radius=10
                            ),
                        ],
                    ),
                    ft.Container(
                        height=200,
                        bgcolor=C["surface2"],
                        border_radius=8,
                        padding=5,
                        content=ft.ListView(
                            controls=self.list_siswa_controls,
                            spacing=8,
                            padding=10,
                        ),
                    ),
                ],
            ),
        )

        def make_field(label, hint, ref):
            return ft.Column(
                controls=[
                    ft.Text(label.upper(), size=10, weight=ft.FontWeight.W_700, color=C["text2"]),
                    ft.TextField(
                        ref=ref, hint_text=hint, bgcolor=C["surface2"], border_color=C["border2"],
                        color=C["text"], border_radius=8,
                        content_padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                    ),
                ],
                spacing=4,
            )
        
        enrollment_card = ft.Container(
            bgcolor=C["surface"],
            border_radius=12,
            padding=16,
            border=ft.border.all(1, C["border"]),
            content=ft.Column(
                spacing=10,
                tight=True,
                controls=[
                    section_title("🤖 Enrollment Siswa Baru"),
                    ft.Row([
                        make_field("Nama Lengkap", "Enter Your Name", self.ref_nama),
                        make_field("NISN", "Enter Your NISN", self.ref_nis),
                    ], wrap=True),
                    ft.Row(
                        spacing=5, 
                        alignment=ft.MainAxisAlignment.START, 
                        controls=[
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("KELAS", size=10, weight="bold", color=C["text2"]),
                                    ft.Dropdown(ref=self.ref_kelas, options=self.get_opsi_kelas(), bgcolor=C["surface2"], border_color=C["border2"], border_radius=8, content_padding=10, hint_text="Pilih", color="black"),
                                ]), 
                                expand=True 
                            ),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("GENDER", size=10, weight="bold", color=C["text2"]),
                                    ft.Dropdown(ref=self.ref_jk, options=[ft.dropdown.Option("Laki-laki"), ft.dropdown.Option("Perempuan")], bgcolor=C["surface2"], border_color=C["border2"], border_radius=8, content_padding=10, hint_text="Pilih", color="black"),
                                ]), 
                                expand=True 
                            ),
                        ]
                    ),
                        ft.Column([
                        ft.Text("WA ORANG TUA", size=10, weight="bold", color=C["text2"]),
                        ft.TextField(ref=self.ref_wa, hint_text="0812...", bgcolor=C["surface2"], border_color=C["border2"], border_radius=8, content_padding=10, text_style=ft.TextStyle(color="black", size=14)),
                    ]),
                    ft.Column(
                        tight=True,
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Foto Referensi", color="black", weight="bold"),
                                    chip("Min. 5 Foto", "purple"),
                                ]
                            ),
                            ft.Container(
                                width=120, height=100,
                                border=ft.border.all(1, C["border2"]),
                                border_radius=8,
                                on_click=self.pilih_foto,
                                ink=True,
                                content=ft.Column(
                                    [ft.Icon(ft.Icons.CAMERA_ALT, size=24), ft.Text("Tap pilih foto", size=10, text_align="center")],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    tight=True
                                )
                            ),
                        ]
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.ElevatedButton("💾 Simpan Data Siswa", on_click=self.proses_simpan, bgcolor=C["blue"], color="white", expand=True),
                        ]
                    ),
                ]
            ),
        )

        # Main view                     
        return ft.Container(
            expand=True,
            bgcolor=C["bg"],
            content=ft.Column(
                spacing=0, 
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text("Data Siswa", size=19, weight=ft.FontWeight.W_700, color=C["text"], width=float("inf")),
                            ],
                        ),
                        bgcolor=C["surface"],
                        border=ft.Border(bottom=ft.BorderSide(1, C["border"])),
                        padding=ft.Padding(left=16, right=16, top=40, bottom=12),
                        width=float("inf")
                    ),
                    
                  
                    ft.Container(
                        padding=20,
                        content=ft.Column([
                            list_card,
                            enrollment_card,
                            ft.Container(height=50)
                        ])
                    )
                ]
            )
        )