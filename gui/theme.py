import tkinter as tk
from tkinter import ttk

# Theme Color Palette
COLORS = {
    "bg_main": "#f1f5f9",
    "bg_card": "#ffffff",
    "sidebar_bg": "#0f172a",
    "sidebar_fg": "#f8fafc",
    "sidebar_active": "#1e293b",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "accent": "#0d9488",
    "success": "#16a34a",
    "warning": "#d97706",
    "danger": "#dc2626",
    "text_dark": "#0f172a",
    "text_muted": "#64748b",
    "border": "#e2e8f0"
}

FONTS = {
    "h1": ("Segoe UI", 18, "bold"),
    "h2": ("Segoe UI", 14, "bold"),
    "h3": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9),
    "metric_val": ("Segoe UI", 20, "bold"),
}

def apply_theme(root: tk.Tk):
    """Configures modern ttk styles across the Tkinter application."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # Global background
    root.configure(bg=COLORS["bg_main"])

    # Frame styles
    style.configure("TFrame", background=COLORS["bg_main"])
    style.configure("Card.TFrame", background=COLORS["bg_card"], relief="flat", borderwidth=1)
    style.configure("Sidebar.TFrame", background=COLORS["sidebar_bg"])
    style.configure("Header.TFrame", background=COLORS["bg_card"])

    # Label styles
    style.configure("TLabel", background=COLORS["bg_main"], foreground=COLORS["text_dark"], font=FONTS["body"])
    style.configure("Card.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_dark"], font=FONTS["body"])
    style.configure("Header.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_dark"], font=FONTS["h1"])
    style.configure("Subtitle.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_muted"], font=FONTS["small"])
    style.configure("Sidebar.TLabel", background=COLORS["sidebar_bg"], foreground=COLORS["sidebar_fg"], font=FONTS["body_bold"])

    # Button styles
    style.configure(
        "Primary.TButton",
        font=FONTS["body_bold"],
        background=COLORS["primary"],
        foreground="#ffffff",
        borderwidth=0,
        padding=(12, 6)
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLORS["primary_hover"]), ("disabled", COLORS["text_muted"])],
        foreground=[("disabled", "#ffffff")]
    )

    style.configure(
        "Accent.TButton",
        font=FONTS["body_bold"],
        background=COLORS["accent"],
        foreground="#ffffff",
        borderwidth=0,
        padding=(12, 6)
    )

    style.configure(
        "Danger.TButton",
        font=FONTS["body_bold"],
        background=COLORS["danger"],
        foreground="#ffffff",
        borderwidth=0,
        padding=(12, 6)
    )

    style.configure(
        "Sidebar.TButton",
        font=FONTS["body"],
        background=COLORS["sidebar_bg"],
        foreground=COLORS["sidebar_fg"],
        borderwidth=0,
        anchor="w",
        padding=(15, 10)
    )
    style.map(
        "Sidebar.TButton",
        background=[("active", COLORS["sidebar_active"])],
        foreground=[("active", "#ffffff")]
    )

    # Entry & Combobox
    style.configure("TEntry", padding=6, font=FONTS["body"])
    style.configure("TCombobox", padding=6, font=FONTS["body"])

    # Treeview style
    style.configure(
        "Treeview",
        font=FONTS["body"],
        rowheight=28,
        background=COLORS["bg_card"],
        fieldbackground=COLORS["bg_card"],
        foreground=COLORS["text_dark"]
    )
    style.configure(
        "Treeview.Heading",
        font=FONTS["body_bold"],
        background="#e2e8f0",
        foreground=COLORS["text_dark"],
        padding=6
    )
    style.map("Treeview", background=[("selected", COLORS["primary"])], foreground=[("selected", "#ffffff")])

class StatCard(ttk.Frame):
    """Reusable GUI card widget for key dashboard metrics."""
    def __init__(self, parent, title: str, value: str, icon_symbol: str = "📊", accent_color: str = COLORS["primary"]):
        super().__init__(parent, style="Card.TFrame", padding=15)
        self.columnconfigure(0, weight=1)

        header_lbl = ttk.Label(self, text=f"{icon_symbol} {title.upper()}", style="Subtitle.TLabel", font=("Segoe UI", 9, "bold"))
        header_lbl.grid(row=0, column=0, sticky="w", pady=(0, 4))

        val_lbl = tk.Label(self, text=str(value), font=FONTS["metric_val"], bg=COLORS["bg_card"], fg=accent_color)
        val_lbl.grid(row=1, column=0, sticky="w")
