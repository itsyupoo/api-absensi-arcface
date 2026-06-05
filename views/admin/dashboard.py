# views/admin/dashboard.py

import flet as ft
import asyncio
import pandas as pd
from components.ui import C, card, stat_box, chip, wa_status_bar, section_title
from database_connect import get_db_connection, ambil_statistik_dashboard, ambil_presensi_terbaru, ambil_rekap_7_hari, hitung_wa_terkirim_hari_ini
from datetime import datetime

class AdminDashboard:
    def __init__(self, page, state, go_to):
        self.page = page
        self.state = state
        self.go_to = go_to

        # Penampung Referensi UI
        self.ref_total = ft.Ref[ft.Text]()
        self.ref_hadir = ft.Ref[ft.Text]()
        self.ref_lambat = ft.Ref[ft.Text]()
        self.ref_belum = ft.Ref[ft.Text]()
        self.ref_list_presensi = ft.Ref[ft.Column]()

        self.ref_bars = [ft.Ref[ft.Container]() for _ in range(7)]
        self.ref_bar_texts = [ft.Ref[ft.Text]() for _ in range(7)]

    def _buat_baris_tabel(self, nama, kelas, jam, status, jenis_kelamin):
        color = "green" if status == "Hadir" else "#FF0800"
        init = nama[0] if nama else "?"
        
        if jenis_kelamin in ["L", "Laki-laki", "Laki-Laki"]:
            path_avatar = "logo_cowok.png"
        else:
            path_avatar = "logo_cewek.png"

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                       content=ft.Image(
                            src=path_avatar,
                            fit=ft.ImageFit.CONTAIN,
                            width=24,
                            height=24,
                        ),
                        width=30, 
                        height=30, 
                        bgcolor=C["surface2"],
                        border_radius=8, 
                        border=ft.border.all(1, C["border"]),
                        alignment=ft.alignment.center,
                    ),    
                    ft.Text(nama, size=12, weight=ft.FontWeight.W_700, color=C["text"], expand=True),
                    ft.Text(kelas, size=11, color=C["text2"], width=70),
                    ft.Text(jam, size=11, color=C["text2"], font_family="monospace", width=52),
                    chip(status, color),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, C["border"])),
            padding=ft.padding.symmetric(vertical=9),
        )

    async def update_dashboard_periodic(self):
        while True:
            try:
                stats = ambil_statistik_dashboard()
                terbaru = ambil_presensi_terbaru(limit=5)

                if self.ref_total.current: self.ref_total.current.value = str(stats['total'])
                if self.ref_hadir.current: self.ref_hadir.current.value = str(stats['hadir'])
                if self.ref_lambat.current: self.ref_lambat.current.value = str(stats['terlambat'])
                if self.ref_belum.current: self.ref_belum.current.value = str(stats['belum'])

                if self.ref_list_presensi.current:
                    self.ref_list_presensi.current.controls.clear()
                    for p in terbaru:
                        jam_str = p['waktu_absen'].strftime("%H:%M")
                        jk = p.get('jenis_kelamin', 'L')
                        self.ref_list_presensi.current.controls.append(
                            self._buat_baris_tabel(p['nama'], p['kelas'], jam_str, p['status'], jk)
                        )
                
                self.page.update()
            except Exception as e:
                print(f"Polling Error: {e}")
            
            await asyncio.sleep(60)

    def proses_export_excel(self, _):
        # 1. Ambil data dari MySQL
        db = get_db_connection() # Fungsi koneksi DB kamu
        if db:
            try:
                cursor = db.cursor(dictionary=True)
                # Query ambil data riwayat presensi hari ini
                query = """
                    SELECT c.waktu_absen, s.nama, s.kelas, 
                           CASE WHEN TIME(c.waktu_absen) <= '07:15:00' THEN 'Hadir' ELSE 'Terlambat' END as status
                    FROM catatan_kehadiran c 
                    JOIN dataset_siswa s ON c.id_siswa = s.id_siswa 
                    ORDER BY c.waktu_absen DESC
                """
                cursor.execute(query)
                data_absen = cursor.fetchall()
                
                if not data_absen:
                    print("Tidak ada data absensi hari ini untuk diekspor.")
                    return
                
                # 2. Ubah data MySQL menjadi DataFrame Pandas
                df = pd.DataFrame(data_absen)

                if 'waktu_absen' in df.columns:
                    df['waktu_absen'] = df['waktu_absen'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Beri nama kolom yang rapi untuk Excel
                df.columns = ['Waktu Presensi', 'Nama Siswa', 'Kelas', 'Status Kehadiran']
                
                # 3. Simpan menjadi file Excel
                nama_file = f"Rekap_Absensi_Siswa.xlsx"

                with pd.ExcelWriter(nama_file, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Absensi Hari Ini')
                    
                    # 👉 PROSES AUTO-FIT: Melebarkan kolom secara otomatis berdasarkan teks terpanjang
                    worksheet = writer.sheets['Absensi Hari Ini']
                    for col in worksheet.columns:
                        max_len = max(len(str(cell.value or '')) for cell in col)
                        col_letter = col[0].column_letter
                        worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

                print(f"🔥 Berhasil! File tersimpan otomatis dan rapi: {nama_file}")
            except Exception as ex:
                    print(f"Gagal ekspor: {ex}")
            finally:
                    cursor.close()
                    db.close()

    def build(self) -> ft.Container:
        # Jalankan background task
        self.page.run_task(self.update_dashboard_periodic)
        total_hari_ini = hitung_wa_terkirim_hari_ini()

        # 1. Stats Row
        stats_row = ft.Row(
            controls=[
                stat_box("0", "Total Siswa", "warn", ref=self.ref_total),
                stat_box("0", "Hadir", "green", ref=self.ref_hadir),
                stat_box("0", "Terlambat", "#FF0800", ref=self.ref_lambat),
                stat_box("0", "Belum Absen", "#FF2400", ref=self.ref_belum),
            ],
            spacing=8,
        )

        rekap_saat_ini = ambil_rekap_7_hari()
        nilai_tertinggi = max([row[1] for row in rekap_saat_ini]) if rekap_saat_ini else 0
        limit_grafik = max(nilai_tertinggi, 40)
        bars_controls = []

        for i, (label, val) in enumerate(rekap_saat_ini):
            # Pastikan indeks i tidak melebihi jumlah ref yang sudah kita buat di __init__
            if i < len(self.ref_bars):
                tinggi_batang = int((val / limit_grafik) * 80) if val > 0 else 4
                bars_controls.append(
                    ft.Column(
                        controls=[
                            ft.Text(str(val) if val > 0 else "", size=9, color=C["text2"], ref=self.ref_bar_texts[i]),
                            ft.Container(
                                width=28, height=tinggi_batang,bgcolor=C["green"] if val > 0 else C["surface3"],border_radius=ft.border_radius.only(top_left=4, top_right=4),ref=self.ref_bars[i],animate_size=ft.Animation(600, ft.AnimationCurve.DECELERATE),
                            ),
                            ft.Text(label, size=9, color=C["text3"]),
                        ],
                        horizontal_alignment="center", spacing=3
                    )
                )

        stats_row = ft.Row([
            stat_box("0", "Total Siswa", "warn", ref=self.ref_total),
            stat_box("0", "Hadir", "green", ref=self.ref_hadir),
            stat_box("0", "Terlambat", "#FF0800", ref=self.ref_lambat),
            stat_box("0", "Belum Absen", "#FF2400", ref=self.ref_belum),
        ], spacing=8)
        
        nama_bulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        sekarang = datetime.now()
        bulan_tahun_str = f"{nama_bulan[sekarang.month - 1]} {sekarang.year}"

        chart_card = ft.Container(
            content=ft.Column([
                ft.Row([section_title("📈 Kehadiran 7 Hari"), chip(bulan_tahun_str, "blue")], alignment="spaceBetween"),
                ft.Container(height=12),
                ft.Row(controls=bars_controls, alignment="spaceBetween", vertical_alignment="end"),
            ]),
            bgcolor=C["surface"], border_radius=12, border=ft.border.all(1, C["border"]), padding=16
        )

        # 3. Recent Log Card (Menggunakan Ref agar bisa diupdate otomatis)
        recent_card = ft.Container(
            content=ft.Column([
                    ft.Row([
                        section_title("📋 5 Presensi Terbaru"),
                        ft.TextButton("Lihat Semua →", on_click=lambda e: self.go_to("/admin", tab=1)),
                        ], alignment="spaceBetween"),
                    ft.Container(height=8), ft.Column(ref=self.ref_list_presensi, spacing=0),
                ],
            ),
            bgcolor=C["surface"], border_radius=12, padding=16,
            border=ft.border.all(1, C["border"]), margin=ft.margin.only(bottom=12),
        )

        # 4. WhatsApp Card
        wa_card = ft.Container(
            content=ft.Column([
                section_title("📱 Gateway WhatsApp"), 
                ft.Container(height=10),  
                wa_status_bar(active=True, total_pesan=total_hari_ini),
            ]),
            bgcolor=C["surface"], border_radius=12, border=ft.border.all(1, C["border"]), padding=16
        )

        # RETURN UTAMA (Pastikan menjorok ke dalam method build)
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text("Dashboard", size=15, weight="bold", color=C["text"]),
                                ft.Text("Ringkasan hari ini", size=11, color=C["text2"]),
                            ], expand=True),
                            ft.Container(content=ft.Text("Export Sheets", size=11, weight= "bold", color="black"), padding=10, border=ft.border.all(1, "black"), border_radius=8, ink=True, on_click=self.proses_export_excel)
                        ]),
                        padding=16, bgcolor=C["surface"], border=ft.border.only(bottom=ft.BorderSide(1, C["border"]))
                    ),
                    # Body
                    ft.Container(
                        content=ft.Column([
                            ft.Container(height=4),
                            stats_row,
                            chart_card,
                            recent_card,
                            wa_card,
                        ], scroll=ft.ScrollMode.AUTO),
                        expand=True, padding=14
                    )
                ], spacing=0
            ), expand=True, bgcolor=C["bg"]
        )