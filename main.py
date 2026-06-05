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
    
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#4F55F7",
            secondary="#4F55F7",
            surface="#FFFFFF",
            background="#FFFFFF",
            error="#F75F5F",
        ),
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
        ("Beranda",   ft.Icons.HOME_ROUNDED,      SiswaDashboard),
        ("Presensi",  ft.Icons.CAMERA_ALT_ROUNDED, SiswaPresensi),
        ("Riwayat",   ft.Icons.LIST_ALT_ROUNDED,   SiswaRiwayat),
        ("Profil",    ft.Icons.PERSON_ROUNDED,      SiswaProfil),
    ]

    content_ref = ft.Ref[ft.Container]()

    def render_tab(idx):
        ViewClass = tabs[idx][2]
        return ViewClass(page, state, go_to).build()

    def on_tab_change(e):
        state["current_tab_siswa"] = e.control.selected_index
        content_ref.current.content = render_tab(e.control.selected_index)
        page.update()

    nav_bar = ft.NavigationBar(
        selected_index=active_tab,
        on_change=on_tab_change,
        bgcolor="#0D47A1",
        indicator_color="#1C6BF4BE",
        surface_tint_color="#0D47A1",
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME_ROUNDED,
                label=t[0],
            )
            for t in tabs
        ],
    )

    body = ft.Container(
        ref=content_ref,
        content=render_tab(active_tab),
        expand=True,
    )

    return ft.View(
        route="/siswa",
        padding=0,
        bgcolor="#0D47A1",
        controls=[
            ft.Column(
                controls=[body, nav_bar],
                expand=True,
                spacing=0,
            )
        ],
    )


# ─────────────────────────────────────────────────────
#  ADMIN SHELL  (layout dengan NavigationRail sidebar)
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
        state["current_tab_admin"] = e.control.selected_index
        content_ref.current.content = render_tab(e.control.selected_index)
        page.update()

    rail = ft.NavigationRail(
        selected_index=active_tab,
        on_change=on_tab_change,
        bgcolor="#0D47A1",
        indicator_color="#1C6BF4BE",
        min_width=64,
        min_extended_width=180,
        label_type=ft.NavigationRailLabelType.ALL,
        destinations=[
            ft.NavigationRailDestination(
                icon=tabs[i][1],
                selected_icon=tabs[i][1],
                label=tabs[i][0],
            )
            for i in range(len(tabs))
        ],
        leading=ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,spacing=4,
                controls=[
                    ft.Container(
                        width=42, height=42, # Ukurannya sedikit diperbesar agar jelas
                        border_radius=21,    # Membuatnya bulat sempurna (setengah dari width)
                        border=ft.border.all(2, "#1C6BF4BE"), # Memberi bingkai biru tipis
                        image=ft.DecorationImage(
                            src="admin_photo.png", # Pastikan file ada di folder /assets
                            fit=ft.ImageFit.COVER,
                    ),
                 ),
                    ft.Text("Administrator", size=10, weight="bold", color="#FFFFFF"),
                ],
            ),
            padding=ft.padding.only(top=16, bottom=8),
        ),
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
        controls=[
            ft.Row(
                controls=[rail, ft.VerticalDivider(width=1, color="#ffffff10"), body],
                expand=True,
                spacing=0,
            )
        ],
    )


ft.app(target=main)
