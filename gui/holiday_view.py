import tkinter as tk
from tkinter import ttk
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS
from utils.helpers import get_current_date

class HolidayViewFrame(ttk.Frame):
    """Reusable Holiday View Frame for Teacher, Student, Parent, and Admin portals."""
    def __init__(self, parent, db_manager: DBManager):
        super().__init__(parent, padding=15)
        self.db = db_manager
        self._build_ui()

    def _build_ui(self):
        # Header Section
        hdr = ttk.Frame(self)
        hdr.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(hdr, text="📅 Official School Holidays", font=FONTS["h1"]).pack(anchor=tk.W)
        ttk.Label(hdr, text="View today's holiday status and official school holidays.", style="Subtitle.TLabel").pack(anchor=tk.W)

        # 1. Today's Holiday Status Card
        today_str = get_current_date()
        today_h = self.db.get_today_holiday(today_str)

        card_title = " 🎉 TODAY'S HOLIDAY " if today_h else " 📅 TODAY'S STATUS "
        status_card = ttk.LabelFrame(self, text=card_title, padding=15)
        status_card.pack(fill=tk.X, pady=(0, 15))

        if today_h:
            ttk.Label(status_card, text=f"🎉 {today_h['title']}", font=("Segoe UI", 14, "bold"), foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(0, 5))
            ttk.Label(status_card, text=f"📅 Date: {today_h['date']}", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(0, 5))
            ttk.Label(status_card, text=f"📢 Announcement / Message: {today_h.get('description', 'Enjoy your holiday! Have a wonderful day.')}", font=FONTS["body"]).pack(anchor=tk.W)
        else:
            ttk.Label(status_card, text=f"📅 No Official Holiday Today ({today_str})", font=FONTS["body_bold"], foreground=COLORS["text_muted"]).pack(anchor=tk.W)
            ttk.Label(status_card, text="Regular academic and school sessions are active.", font=FONTS["body"]).pack(anchor=tk.W)

        # 2. Holidays & Activities Notebook
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: School Holidays
        tab_h = ttk.Frame(notebook, padding=10)
        notebook.add(tab_h, text="📅 School Holidays")

        all_holidays = self.db.get_all_holidays()

        # Visual Cards Section for all Admin-created holidays
        if all_holidays:
            cards_frame = ttk.Frame(tab_h)
            cards_frame.pack(fill=tk.X, pady=(0, 10))

            canvas = tk.Canvas(cards_frame, height=140, highlightthickness=0)
            scrollbar = ttk.Scrollbar(cards_frame, orient="vertical", command=canvas.yview)
            scroll_content = ttk.Frame(canvas)

            scroll_content.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            canvas.create_window((0, 0), window=scroll_content, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            for h in all_holidays:
                c = ttk.LabelFrame(scroll_content, text=f" 🎉 Holiday: {h['title']} ", padding=10)
                c.pack(fill=tk.X, expand=True, pady=4, padx=5)

                ttk.Label(c, text=f"🎉 {h['title']}", font=("Segoe UI", 12, "bold"), foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(0, 2))
                ttk.Label(c, text=f"📅 Date: {h['date']}", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(0, 2))
                ttk.Label(c, text=f"📢 Description: {h.get('description', 'N/A')}", font=FONTS["body"], wraplength=700, justify=tk.LEFT).pack(anchor=tk.W)
        else:
            no_h_frame = ttk.LabelFrame(tab_h, text=" 📅 School Holidays ", padding=15)
            no_h_frame.pack(fill=tk.X, pady=(0, 10))
            ttk.Label(no_h_frame, text="No holidays announced yet.", font=FONTS["body_bold"], foreground=COLORS["text_muted"]).pack(anchor=tk.W)

        tbl_frame = ttk.Frame(tab_h)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("title", "date", "description")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=8)

        tree.heading("title", text="Holiday Name")
        tree.heading("date", text="Holiday Date")
        tree.heading("description", text="Description")

        tree.column("title", width=220, anchor="w")
        tree.column("date", width=140, anchor="center")
        tree.column("description", width=420, anchor="w")

        sb = ttk.Scrollbar(tbl_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        for h in all_holidays:
            tree.insert("", tk.END, values=(
                h['title'], h['date'], h.get('description', 'N/A')
            ))

        # Tab 2: School Activities
        tab_a = ttk.Frame(notebook, padding=10)
        notebook.add(tab_a, text="🎈 School Activities")

        act_tbl_frame = ttk.Frame(tab_a)
        act_tbl_frame.pack(fill=tk.BOTH, expand=True)

        act_cols = ("title", "date", "description")
        act_tree = ttk.Treeview(act_tbl_frame, columns=act_cols, show="headings", height=8)

        act_tree.heading("title", text="Activity Name")
        act_tree.heading("date", text="Activity Date")
        act_tree.heading("description", text="Description")

        act_tree.column("title", width=220, anchor="w")
        act_tree.column("date", width=140, anchor="center")
        act_tree.column("description", width=420, anchor="w")

        act_sb = ttk.Scrollbar(act_tbl_frame, orient="vertical", command=act_tree.yview)
        act_tree.configure(yscroll=act_sb.set)
        act_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        act_sb.pack(side=tk.RIGHT, fill=tk.Y)

        activities = self.db.get_all_activities()
        for a in activities:
            act_tree.insert("", tk.END, values=(
                a['title'], a['date'], a.get('description', 'N/A')
            ))

