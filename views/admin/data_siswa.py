# views/admin/data_siswa.py

import flet as ft
from components.ui import C, chip, section_title
from database_connect import simpan_siswa, ambil_semua_wajah
import json
from deepface import DeepFace


class AdminDataSiswa:
    def __init__(self, page, state, go_to):
        self.page  = page
        self.state = state
        self.go_to = go_to
        self.photo_slots = [False, False, False, False, False]
        self.photo_refs  = [ft.Ref[ft.Container]() for _ in range(5)]

        self.file_picker = ft.FilePicker(on_result=self.handle_file_result)
        self.page.overlay.append(self.file_picker)

        self.ref_nama = ft.Ref[ft.TextField]()
        self.ref_nis  = ft.Ref[ft.TextField]()
        self.ref_wa   = ft.Ref[ft.TextField]() 
        self.ref_kelas = ft.Ref[ft.Dropdown]()
        self.ref_jk = ft.Ref[ft.Dropdown]()

        self.list_siswa_container = ft.Ref[ft.Column]()
        self.count_text_ref = ft.Ref[ft.Text]()
        

    def _snack(self, msg, color="green"):
        snack = ft.SnackBar(
            content=ft.Text(msg, color="white", weight="bold"),bgcolor=color,behavior=ft.SnackBarBehavior.FLOATING,duration=3000)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
        print(f">>> DEBUG SnackBar: {msg}")

    def refresh_data(self):
        """Mengambil data terbaru dari DB dan memperbarui UI secara real-time"""
        try:
            data_db = ambil_semua_wajah()
            total_siswa = len(data_db)
            if self.count_chip_ref.current:
                self.count_chip_ref.current.content.value = f"{total_siswa} Siswa"

            new_rows = []
            for s in data_db:
                jk = s.get('jenis_kelamin', 'Laki-laki')
                path_logo = "/logo_cowok.png" if jk == "Laki-laki" else "/logo_cewek.png"
                
                row = self.siswa_row(
                    path_logo, 
                    s.get('nama', 'Tanpa Nama'), 
                    s.get('nis', '-'), 
                    s.get('kelas', 'Kelas ?'), 
                    s.get('wa_ortu', '-')
                )
                new_rows.append(row)  
            if self.list_siswa_container.current:
                self.list_siswa_container.current.controls = new_rows      

            self.page.update()
            print(f">>> DEBUG: UI Updated. Total: {total_siswa}")
        except Exception as e:
            print(f"Error refresh data: {e}")
            

    def siswa_row(self, path_logo, nama, nis, kelas, wa):
        """Template untuk baris siswa"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Image(src=path_logo, width=24, height=24, fit="contain"),
                        width=36, height=36, bgcolor=C["surface2"], border_radius=10, alignment="center"
                    ),
                    ft.Column(controls=[
                        ft.Text(nama, size=13, weight=ft.FontWeight.W_700, color=C["text"]),
                        ft.Text(f"NIS: {nis} • Kelas : {kelas} • WA: {wa}", size=11, color=C["text2"]),
                    ], spacing=1, expand=True),
                ]
            ),
            margin=ft.Margin(bottom=8)
        )
    
    def filter_pencarian(self, e):
        query = e.control.value.lower()
        data_db = ambil_semua_wajah()
        
        filtered_rows = []
        for s in data_db:
            nama = s.get('nama', '').lower()
            nis = str(s.get('nis', '')).lower()
            kelas = s.get('kelas', '').lower()
            
            if query in nama or query in nis or query in kelas:
                jk = s.get('jenis_kelamin', 'Laki-laki')
                path_logo = "/logo_cowok.png" if jk == "Laki-laki" else "/logo_cewek.png"
                
                filtered_rows.append(self.siswa_row(
                    path_logo, 
                    s.get('nama'), s.get('nis'), s.get('kelas'), s.get('wa_ortu')))
        
        if self.list_siswa_container.current:
            self.list_siswa_container.current.controls = filtered_rows
            
        if self.count_text_ref.current:
            self.count_text_ref.current.value = f"{len(filtered_rows)} Ditemukan"
            
        self.page.update()

    def pilih_foto(self, e):
        self.page.update() 
        self.file_picker.pick_files(allow_multiple=True,file_type=ft.FilePickerFileType.IMAGE)
            
    def handle_file_result(self, e):
        """Menangani hasil pilihan foto dari galeri"""
        if e.files:
            jumlah_foto = len(e.files)
            self._snack(f"✅ {jumlah_foto} foto terpilih.")
            self.state['selected_images'] = [f.path for f in e.files]

            for i in range(5):
                if i < jumlah_foto:
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

    def mulai_training(self, e):
        """Fungsi untuk memproses foto galeri menjadi embedding ArcFace (Centroid)"""
        images = self.state.get('selected_images', [])
        
        if not images:
            self._snack("❌ Pilih foto dulu sebelum training!", color="red")
            return
        
        # Matikan tombol agar tidak diklik berkali-kali saat proses
        e.control.disabled = True
        self.page.update()

        self._snack("🤖 Memulai training... Mohon tunggu.", color="blue") 
        
        try:
            all_embeddings = []
            
            for path in images:
                # Logika utama ArcFace kamu
                res = DeepFace.represent(
                    img_path=path, 
                    model_name="ArcFace", 
                    detector_backend="mtcnn",
                    enforce_detection=True
                )
                all_embeddings.append(res[0]["embedding"])

            if all_embeddings:
                import numpy as np
                centroid = np.mean(all_embeddings, axis=0)
                self.state['current_face_vector'] = centroid.tolist() 
                self._snack(f"✅ Berhasil memproses {len(images)} foto menjadi Centroid!", color="green")
            
        except Exception as err:
            print(f"Error Training: {err}")
            self._snack("❌ Gagal mendeteksi wajah di salah satu foto.", color="red")
        
        finally:
            e.control.disabled = False
            self.page.update()

    def proses_simpan(self, e):
        """Menyimpan data teks dan face_embedding asli ke MySQL"""
        print(">>> DEBUG: Tombol Simpan diklik!")
        
        # Validasi input
        nama = self.ref_nama.current.value
        nis = self.ref_nis.current.value
        face_vector = self.state.get('current_face_vector', None)

        if not nama or not nis:
            self._snack("⚠️ Nama dan NISN wajib diisi!", color="orange")
            return

        if face_vector is None:
            self._snack("⚠️ Klik tombol 'Training' dulu untuk memproses wajah!", color="orange")
            return

        e.control.disabled = True
        self.page.update()
        
        try:
            kelas = self.ref_kelas.current.value 
            wa = self.ref_wa.current.value
            jk = self.ref_jk.current.value

           
            berhasil = simpan_siswa(nis, nama, kelas, wa, face_vector, jk)
            
            if berhasil:    
                self._snack(f"✅ Data {nama} berhasil disimpan ke MySQL!", color="green")
              
                self.ref_nama.current.value = ""
                self.ref_nis.current.value = ""
                self.ref_wa.current.value = ""
                self.state['current_face_vector'] = None
                self.state['selected_images'] = []
                self.refresh_data() 
            else:
                self._snack("❌ Gagal simpan! Cek koneksi database.", color="red")
                
        except Exception as err:
            print(f">>> ERROR FATAL: {err}")
            self._snack(f"⚠️ Kesalahan sistem: {str(err)}", color="red")
    
        finally:
            e.control.disabled = False 
            self.page.update()

    def build(self) -> ft.Container:
        data_db = ambil_semua_wajah()
        total_awal = len(data_db)

        # ── Daftar siswa card ──
        list_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            section_title("👥 Daftar Siswa"),
                            ft.Container(
                                content=ft.Text(f"{total_awal} Siswa", ref=self.count_text_ref, size=11, color="white", weight="bold"),
                                bgcolor="blue", padding=ft.Padding(left=8, right=9, top=2, bottom=2), border_radius=10
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=10),
                    ft.TextField(
                        hint_text="Cari nama atau NISN...",
                        bgcolor=C["surface2"], border_color=C["border2"], color=C["text"], border_radius=8,
                        content_padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                        on_change=self.filter_pencarian),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.ListView(
                        ref=self.list_siswa_container,expand=True,spacing=8,
                        controls=[
                            self.siswa_row(
                                "/logo_cowok.png" if s.get('jenis_kelamin')=="Laki-laki" else "/logo_cewek.png",
                                s.get('nama'), s.get('nis'), s.get('kelas'), s.get('wa_ortu')
                            ) for s in data_db
                        ],
                    ),
                height=300,
            ),
        ],
        spacing=0,
    ),
     bgcolor=C["surface"], 
     border_radius=12, 
     border=ft.border.all(1, C["border"]),
     padding=16, 
     margin=ft.Margin(bottom=12))

        # ── Enrollment form card (BAGIAN PANJANG) ──
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
                spacing=4, expand=True
            )
        
        photo_grid_controls = [
            ft.Container(
                ref=self.photo_refs[i],
                content=ft.Text("✅" if self.photo_slots[i] else "📷", size=20),
                width=52, height=52, border_radius=10,
                bgcolor=C["blue_dim"] if self.photo_slots[i] else C["surface2"],
                alignment="center",
            ) for i in range(5)
        ]

        enrollment_card = ft.Container(
            content=ft.Column(
                controls=[
                    section_title("🤖 Enrollment Siswa Baru"),
                    ft.Container(height=12),
                    ft.Row(controls=[
                        make_field("Nama Lengkap", "Enter Your Name", self.ref_nama),
                        ft.Container(width=10),
                        make_field("NISN", "Enter Your NISN", self.ref_nis),
                    ]),
                    ft.Container(height=8),
                    ft.Row(controls=[
                        ft.Column(controls=[
                            ft.Text("KELAS", size=10, weight="bold", color=C["text2"]),
                            ft.Dropdown(
                                ref=self.ref_kelas, value="XI IPA 1", bgcolor=C["surface2"],
                                border_color=C["border2"], color="black", text_style=ft.TextStyle(color="black"), border_radius=8,
                                options=[ft.dropdown.Option(key=f"XI IPA {i+1}", text=f"XI IPA {i+1}", content=ft.Text(f"XI IPA {i+1}", color="black")) for i in range(7)]
                            ),
                        ], expand=True),
                        ft.Container(width=10),
                        ft.Column(controls=[
                            ft.Text("JENIS KELAMIN", size=10, weight="bold", color=C["text2"]),
                            ft.Dropdown(
                                ref=self.ref_jk, value="Laki-laki", bgcolor=C["surface2"],
                                border_color=C["border2"], color="black", text_style=ft.TextStyle(color="black"), border_radius=8,
                                options=[ft.dropdown.Option("Laki-laki"), ft.dropdown.Option("Perempuan")]
                            ),
                        ], expand=True),
                        ft.Container(width=10),
                        make_field("Nomor WhatsApp Orang Tua", "08**********", self.ref_wa),
                    ]),
                    ft.Container(height=12),
                    # Bagian Upload Foto
                    ft.Container(
                        content=ft.Column(controls=[
                            ft.Row([ft.Text("Foto Referensi", color="black", weight="bold", expand=True), chip("Min. 5 Foto", "purple")]),
                            ft.Container(
                                content=ft.Column([ft.Text("📸", size=28), ft.Text("Tap untuk pilih foto", size=11)], horizontal_alignment="center"),
                                border=ft.border.all(2, C["border2"]), border_radius=10, padding=15, 
                                on_click=self.pilih_foto, ink=True
                            ),
                            ft.Container(height=10),
                            ft.Row(controls=photo_grid_controls, spacing=8),
                        ]),
                        bgcolor=C["surface2"], padding=12, border_radius=10
                    ),
                    ft.Container(height=12),
                    ft.Row(controls=[
                        ft.Container(content=ft.Text("💾 Simpan", color="white", weight="bold"), bgcolor=C["blue"], 
                                     expand=True, padding=12, border_radius=8, on_click=self.proses_simpan, ink=True),
                        ft.Container(content=ft.Text("🤖 Training", color="white", weight="bold"), bgcolor=C["purple"], 
                                     expand=True, padding=12, border_radius=8, on_click=self.mulai_training, ink=True),
                    ], spacing=10),
                ]
            ),
            bgcolor=C["surface"], border_radius=12, padding=16, border=ft.border.all(1, C["border"])
        )

        return ft.Container(
    content=ft.Column(
        controls=[
            
            ft.Container(
                content=ft.Text("Data Siswa", size=15, weight="bold"), 
                padding=15
            ),
            
            
            ft.Container(
                content=ft.Column(
                    controls=[list_card, enrollment_card], 
                    scroll=ft.ScrollMode.AUTO, 
                    expand=True
                ),
                padding=14,  
                expand=True  
            ),
        ],
        spacing=0
    ),
    expand=True, 
    bgcolor=C["bg"]
)