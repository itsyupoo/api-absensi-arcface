import flet as ft
from views.login import LoginView
from views.siswa.dashboard import SiswaDashboard
from views.siswa.presensi import SiswaPresensi
from views.siswa.riwayat import SiswaRiwayat
from views.siswa.profil import SiswaProfil
from views.admin.dashboard import AdminDashboard
from views.admin.monitoring import AdminMonitoring
from views.admin.data_siswa import AdminDataSiswa
from views.admin.settings import AdminSettings


def main(page: ft.Page):
    page.title = "Presensi SMA Sjakhyakirti"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#FFFFFF"
    page.padding = 0
    screen_width = page.width or 1200
    if screen_width < 600:
        page.theme = ft.Theme(visual_density=ft.VisualDensity.COMPACT)
        page.zoom = 0.85
    else:
        page.theme = ft.Theme(visual_density=ft.VisualDensity.STANDARD)
        page.zoom = 1.0
        # Menggabungkan skema warna primer/sekunder milikmu ke dalam tema
        page.theme.color_scheme = ft.ColorScheme(
        primary="#4F55F7",
        secondary="#4F55F7",
        surface="#FFFFFF",
        error="#F75F5F",
    )

    # ── state global ──
    state = {
        "user_role": None,
        "user_data": None,
        "current_tab_siswa": 0,
        "current_tab_admin": 0,
    }

    def route_change(e=None):
        page.views.clear()
        route = page.route

        if route == "/" or route == "/login":
            page.views.append(LoginView(page, state, go_to).build())

        elif route == "/siswa":
            page.views.append(
                build_siswa_shell(page, state, go_to, state["current_tab_siswa"])
            )
        elif route == "/admin":
            page.views.append(
                build_admin_shell(page, state, go_to, state["current_tab_admin"])
            )
        else:
            page.views.append(LoginView(page, state, go_to).build())
        page.update()

    def go_to(route, tab=None):
        if tab is not None:
            if "siswa" in route:
                state["current_tab_siswa"] = tab
            else:
                state["current_tab_admin"] = tab
        page.route = route
        route_change()
        
    page.on_route_change = route_change
    page.go("/login")


# ─────────────────────────────────────────────────────
#  SISWA SHELL  (layout dengan BottomNavigationBar)
# ─────────────────────────────────────────────────────
def build_siswa_shell(page, state, go_to, active_tab=0):
    tabs = [
        ("Beranda",  ft.Icons.HOME_ROUNDED,      SiswaDashboard),
        ("Presensi", ft.Icons.CAMERA_ALT_ROUNDED, SiswaPresensi),
        ("Riwayat",  ft.Icons.LIST_ALT_ROUNDED,   SiswaRiwayat),
        ("Profil",   ft.Icons.PERSON_ROUNDED,    SiswaProfil),
    ]

    content_ref = ft.Ref[ft.Container]()

    def render_tab(idx):
        try:
            ViewClass = tabs[idx][2]
            instance = ViewClass(page, state, go_to)
            content = instance.build()
            if content is None:
                print(f"DEBUG: Error - Build mengembalikan None untuk tab {idx}")
                return ft.Text("Gagal memuat konten")
            return content
        except Exception as e:
            print(f"DEBUG: Error render_tab: {e}")
            return ft.Container(content=ft.Text(f"Error: {e}"), bgcolor="red") # Biar kelihatan errornya

    # --- MASUKKAN DI SINI (Ganti yang lama dengan ini) ---
    def on_tab_change(e):
        idx = e.control.selected_index
        state["current_tab_siswa"] = idx
                
        if content_ref.current:
            content_ref.current.content = render_tab(idx)
            content_ref.current.update() 
            page.update()
        else:
            print("DEBUG: ERROR - Ref tidak ditemukan!")
        
    #!!!INI JANGAN DIUCAK-UCAKK KARNO NAVIGASI BAR BAWAHHNYOOO!!!!!!
    nav_bar = ft.NavigationBar(
        selected_index=active_tab,
        on_change=on_tab_change,
        bgcolor="#0D47A1",
        destinations=[
            ft.NavigationBarDestination(
            icon=[ft.Icons.HOME_OUTLINED, ft.Icons.CAMERA_ALT_OUTLINED, ft.Icons.LIST_ALT_OUTLINED, ft.Icons.PERSON_OUTLINED][i],
            selected_icon=[ft.Icons.HOME_ROUNDED, ft.Icons.CAMERA_ALT, ft.Icons.LIST_ALT, ft.Icons.PERSON_ROUNDED][i],
            label=t[0]
        ) for i, t in enumerate(tabs)
    ],
)

    # 2. Body (Gunakan expand=True agar mengisi ruang tersisa)
    body = ft.Container(
        ref=content_ref,
        content=render_tab(active_tab),
        expand=True,
    )

    # 3. View dengan atribut navigasi bawaan
    return ft.View(
        route="/siswa",
        padding=0,
        bgcolor="#0D47A1",
        navigation_bar=nav_bar, # <--- Pasang langsung di sini!
        controls=[
            ft.Column(
                controls=[body],
                expand=True, # <--- Ini yang penting agar body mengisi ruang
            ),
        ],
    )
# ─────────────────────────────────────────────────────
#  ADMIN SHELL  (layout dengan NavigationBar)
# ─────────────────────────────────────────────────────
def build_admin_shell(page, state, go_to, active_tab=0):
    tabs = [
        ("Dashboard",   ft.Icons.DASHBOARD_ROUNDED,    AdminDashboard),
        ("Monitoring",  ft.Icons.MONITOR_ROUNDED,       AdminMonitoring),
        ("Data Siswa",  ft.Icons.PEOPLE_ROUNDED,        AdminDataSiswa),
        ("Settings",    ft.Icons.SETTINGS_ROUNDED,      AdminSettings),
    ]

    content_ref = ft.Ref[ft.Container]()

    def render_tab(idx):
        ViewClass = tabs[idx][2]
        return ViewClass(page, state, go_to).build()

    def on_tab_change(e):
        page.overlay.clear()
        state["current_tab_admin"] = e.control.selected_index
        content_ref.current.content = render_tab(e.control.selected_index)
        page.update()

    nav_bar = ft.NavigationBar(
            selected_index=active_tab,
            on_change=on_tab_change,
            bgcolor="#0D47A1", # Sesuaikan dengan warna tema kamu
            destinations=[
                ft.NavigationBarDestination(
                    icon=tabs[i][1],
                    label=tabs[i][0]
                ) for i in range(len(tabs))
            ],
        )

    body = ft.Container(
        ref=content_ref,
        content=render_tab(active_tab),
        expand=True,
        bgcolor="#07090F",
    )

    return ft.View(
        route="/admin",
        padding=0,
        bgcolor="#3366FF",
        navigation_bar=nav_bar,
        controls=[body],
    )


if __name__ == "__main__":
    ft.app(
        target=main, 
        assets_dir="assets", # Mengunci folder logo/gambar agar ikut terbawa ke APK
        view=ft.AppView.WEB_BROWSER, # Diperlukan untuk simulasi multi-device via IP
    )
