# components/ui.py
# Komponen reusable untuk seluruh aplikasi

import flet as ft

# ── Warna tema ──
C = {
    "bg":         "#F5F5F5",
    "surface":    "#FFFFFF",
    "surface2":   "#FFFFFF",
    "surface3":   "#FFFFFF",
    "border":     "#D1D1D1",
    "border2":    "#1A3A6E",
    "blue":       "#0D47A1",
    "blue_dim":   "#0D47A120",
    "green":      "#22D3A0",
    "green_dim":  "#22D3A01F",
    "red":        "#F75F5F",
    "red_dim":    "#F75F5F1F",
    "warn":       "#1A1A1A",
    "warn_dim":   "#1A1A1A",
    "purple":     "#A78BFA",
    "purple_dim": "#A78BFA1F",
    "text":       "#1A1A1A",
    "text2":      "#1A1A1A",
    "text3":      "#1A1A1A",
}


def chip(label: str, color: str = "blue") -> ft.Container:
    """Badge/pill chip kecil."""
    fg = C.get(color, C["blue"])
    bg = C.get(f"{color}_dim", C["blue_dim"])
    return ft.Container(
        content=ft.Text(label, size=11, weight=ft.FontWeight.W_700, color=fg),
        bgcolor=bg,
        border_radius=99,
        padding=ft.padding.symmetric(horizontal=10, vertical=3),
        border=ft.border.all(1, f"{fg}40"),
    )


def section_title(text: str) -> ft.Text:
    return ft.Text(text, size=14, weight=ft.FontWeight.W_700, color=C["text"])


def label_text(text: str) -> ft.Text:
    return ft.Text(text, size=12, color=C["text2"])


def divider() -> ft.Divider:
    return ft.Divider(height=1, color=C["border"])


def card(content, padding=16) -> ft.Container:
    """Card dengan background surface dan border tipis."""
    return ft.Container(
        content=content,
        bgcolor=C["surface"],
        border_radius=12,
        border=ft.border.all(1, C["border"]),
        padding=padding,
        margin=ft.margin.only(bottom=12),
    )


def stat_box(number: str, label: str, color: str = "blue", ref=None) -> ft.Container:
    """Kotak statistik kecil."""
    fg = C.get(color, C["blue"])
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(number, ref=ref, size=26, weight=ft.FontWeight.W_800, color=fg),
                ft.Text(label, size=11, color=C["text2"]),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=C["surface2"],
        border_radius=10,
        border=ft.border.all(1, C["border"]),
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        expand=True,
        alignment=ft.alignment.center,
    )


def primary_button(text: str, on_click=None, icon=None, disabled=False) -> ft.Container:
    """Tombol utama biru besar."""
    return ft.Container(
        content=ft.Row(
            controls=[
                *(
                    [ft.Icon(icon, color="#FFFFFF", size=20)]
                    if icon else []
                ),
                ft.Text(
                    text,
                    size=15,
                    weight=ft.FontWeight.W_800,
                    color="#1A3A6E" if not disabled else C["text3"],
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor="#1A4BD4" if not disabled else C["surface3"],
        border_radius=12,
        padding=ft.padding.symmetric(vertical=16),
        on_click=on_click if not disabled else None,
        ink=True,
        shadow=ft.BoxShadow(
            blur_radius=20,
            color="#4F8EF740",
            offset=ft.Offset(0, 6),
        ) if not disabled else None,
        margin=ft.margin.only(bottom=12),
    )


def secondary_button(text: str, on_click=None) -> ft.Container:
    """Tombol sekunder transparan."""
    return ft.Container(
        content=ft.Text(text, size=13, weight=ft.FontWeight.W_600, color=C["text2"]),
        border_radius=8,
        border=ft.border.all(1, C["border2"]),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        on_click=on_click,
        ink=True,
    )


def topbar(title: str, subtitle: str = "", actions=None) -> ft.Container:
    """AppBar custom."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(title, size=16, weight=ft.FontWeight.W_700,
                                color=C["text"]),
                        *(
                            [ft.Text(subtitle, size=11, color=C["text2"])]
                            if subtitle else []
                        ),
                    ],
                    spacing=1,
                    expand=True,
                ),
                *(actions or []),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=C["surface"],
        border=ft.border.only(bottom=ft.BorderSide(1, C["border"])),
        padding=ft.padding.symmetric(horizontal=18, vertical=12),
    )


def avatar(initials: str, size: int = 48) -> ft.Container:
    """Avatar lingkaran dengan inisial."""
    return ft.Container(
        content=ft.Text(
            initials[:2].upper(),
            size=size // 3,
            weight=ft.FontWeight.W_800,
            color="#FFFFFF",
            text_align=ft.TextAlign.CENTER,

        ),

        width=size,
        height=size,
        border_radius=size // 4,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#1A3A6E", "#4F8EF7"],

        ),

        alignment=ft.alignment.center,

    )

def geo_indicator(inside: bool = True) -> ft.Container:
    """Indikator status geofencing."""
    color = C["green"] if inside else C["red"]
    bg    = C["green_dim"] if inside else C["red_dim"]
    text  = "Di dalam radius sekolah" if inside else "Di luar radius sekolah!"
    dist  = "± 48 m" if inside else "± 1.2 km"
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    width=8, height=8,
                    border_radius=99,
                    bgcolor=color,
                ),
                ft.Text(text, size=12, weight=ft.FontWeight.W_600, color=color,
                        expand=True),
                ft.Text(dist, size=11, color=color, opacity=0.7),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=bg,
        border_radius=8,
        border=ft.border.all(1, f"{color}30"),
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        margin=ft.margin.only(bottom=12),
    )


def wa_status_bar(active: bool = True, total_pesan: int = 0) -> ft.Container:
    """Status bar WhatsApp Gateway dengan data real-time."""
    color = C["green"] if active else C["red"]
    title = "Terhubung · Fonnte API" if active else "Tidak Terhubung"
    sub   = f"{total_pesan} pesan terkirim hari ini" if active else "Periksa koneksi gateway"
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    width=9, height=9,
                    border_radius=99,
                    bgcolor=color,
                ),
                ft.Column(
                    controls=[
                        ft.Text(title, size=13, weight=ft.FontWeight.W_700, color=color),
                        ft.Text(sub, size=11, color=C["text2"]),
                    ],
                    spacing=1,
                    expand=True,
                ),
                ft.Text(str(total_pesan) if active else "0", size=20, weight=ft.FontWeight.W_800, color=color),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=C["green_dim"] if active else C["red_dim"],
        border_radius=10,
        border=ft.border.all(1, f"{color}30"),
        padding=ft.padding.symmetric(horizontal=14, vertical=12),
    )


def field_input(label: str, hint: str = "", password: bool = False,
                value: str = "", ref=None) -> ft.Column:
    """Input field berlabel."""
    return ft.Column(
        controls=[
            ft.Text(label.upper(), size=11, weight=ft.FontWeight.W_700,
                    color=C["text2"]),
            ft.TextField(
                hint_text=hint,
                password=password,
                can_reveal_password=password,
                value=value,
                ref=ref,
                bgcolor=C["surface2"],
                border_color=C["border2"],
                focused_border_color=C["blue"],
                color=C["text"],
                hint_style=ft.TextStyle(color=C["text3"]),
                border_radius=8,
                content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
            ),
        ],
        spacing=6,
        expand=True,
    )


def info_row(key: str, value: str, value_color: str = None) -> ft.Container:
    """Baris info key-value."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(key, size=12, color=C["text2"], expand=True),
                ft.Text(
                    value,
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=value_color or C["text"],
                ),
            ],
        ),
        border=ft.border.only(bottom=ft.BorderSide(1, C["border"])),
        padding=ft.padding.symmetric(vertical=9),
    )


def scrollable_page(controls: list, padding: int = 16) -> ft.Column:
    """Wrapper halaman yang bisa di-scroll."""
    return ft.Column(
        controls=controls,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
