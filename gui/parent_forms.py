import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS
from utils.validators import validate_email, validate_phone

class ParentFormDialog(tk.Toplevel):
    """Dialog for Admin to Add or Edit Parent details."""
    def __init__(self, parent_win, db_manager: DBManager, parent_id_code: str = None, on_save_callback=None):
        super().__init__(parent_win)
        self.db = db_manager
        self.parent_id_code = parent_id_code
        self.is_edit = parent_id_code is not None
        self.on_save = on_save_callback

        self.title("Edit Parent Record" if self.is_edit else "Add New Parent")
        self.geometry("520x560")
        self.resizable(False, False)
        self.transient(parent_win)
        self.grab_set()

        self.verified_student = None
        self._build_ui()
        if self.is_edit:
            self._load_parent_data()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_text = "✏️ Edit Parent Record" if self.is_edit else "➕ Add New Parent"
        ttk.Label(main_frame, text=title_text, font=FONTS["h2"]).pack(anchor=tk.W, pady=(0, 15))

        f = ttk.Frame(main_frame)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="Parent ID Code *:", font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", pady=6)
        self.entry_pid = ttk.Entry(f, width=28)
        self.entry_pid.grid(row=0, column=1, sticky="w", pady=6, padx=10)
        if self.is_edit:
            self.entry_pid.config(state="disabled")

        ttk.Label(f, text="Parent Full Name *:", font=FONTS["body_bold"]).grid(row=1, column=0, sticky="w", pady=6)
        self.entry_name = ttk.Entry(f, width=28)
        self.entry_name.grid(row=1, column=1, sticky="w", pady=6, padx=10)

        # Linked Student ID with verify button
        ttk.Label(f, text="Link Child Student ID *:", font=FONTS["body_bold"]).grid(row=2, column=0, sticky="w", pady=6)
        sid_frame = ttk.Frame(f)
        sid_frame.grid(row=2, column=1, sticky="w", pady=6, padx=10)

        self.entry_sid = ttk.Entry(sid_frame, width=18)
        self.entry_sid.pack(side=tk.LEFT)

        btn_verify = ttk.Button(sid_frame, text="Verify", command=self.verify_student)
        btn_verify.pack(side=tk.LEFT, padx=5)

        self.lbl_verify_status = ttk.Label(f, text="Waiting for verification...", font=FONTS["small"], foreground=COLORS["text_muted"])
        self.lbl_verify_status.grid(row=3, column=1, sticky="w", padx=10)

        ttk.Label(f, text="Relationship:", font=FONTS["body_bold"]).grid(row=4, column=0, sticky="w", pady=6)
        self.combo_relation = ttk.Combobox(f, values=["Father", "Mother", "Guardian"], state="readonly", width=25)
        self.combo_relation.set("Father")
        self.combo_relation.grid(row=4, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Phone Number *:", font=FONTS["body_bold"]).grid(row=5, column=0, sticky="w", pady=6)
        self.entry_phone = ttk.Entry(f, width=28)
        self.entry_phone.grid(row=5, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Email Address:", font=FONTS["body_bold"]).grid(row=6, column=0, sticky="w", pady=6)
        self.entry_email = ttk.Entry(f, width=28)
        self.entry_email.grid(row=6, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Address:", font=FONTS["body_bold"]).grid(row=7, column=0, sticky="w", pady=6)
        self.entry_address = ttk.Entry(f, width=28)
        self.entry_address.grid(row=7, column=1, sticky="w", pady=6, padx=10)

        btn_bar = ttk.Frame(main_frame)
        btn_bar.pack(fill=tk.X, pady=(20, 0))

        btn_save = ttk.Button(btn_bar, text="💾 Save Record", style="Primary.TButton", command=self.save_parent)
        btn_save.pack(side=tk.RIGHT, padx=5)

        btn_cancel = ttk.Button(btn_bar, text="Cancel", command=self.destroy)
        btn_cancel.pack(side=tk.RIGHT, padx=5)

    def verify_student(self):
        sid = self.entry_sid.get().strip()
        if not sid:
            self.lbl_verify_status.config(text="❌ Please enter a Student ID.", foreground=COLORS["danger"])
            self.verified_student = None
            return

        student = self.db.get_student(sid)
        if student:
            self.lbl_verify_status.config(text=f"✓ Student Found: {student['name']} ({sid})", foreground=COLORS["success"])
            self.verified_student = student
        else:
            self.lbl_verify_status.config(text="❌ Student ID not found in database.", foreground=COLORS["danger"])
            self.verified_student = None

    def _load_parent_data(self):
        p = self.db.get_parent_by_id_code(self.parent_id_code)
        if not p:
            return

        self.entry_pid.config(state="normal")
        self.entry_pid.delete(0, tk.END)
        self.entry_pid.insert(0, p.get('parent_id_code', ''))
        self.entry_pid.config(state="disabled")

        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, p.get('name', ''))

        sid = p.get('student_id', '')
        self.entry_sid.delete(0, tk.END)
        self.entry_sid.insert(0, sid)
        if sid:
            self.verify_student()

        self.combo_relation.set(p.get('relationship', 'Father'))

        self.entry_phone.delete(0, tk.END)
        self.entry_phone.insert(0, p.get('phone', ''))

        self.entry_email.delete(0, tk.END)
        self.entry_email.insert(0, p.get('email', ''))

        self.entry_address.delete(0, tk.END)
        self.entry_address.insert(0, p.get('address', ''))

    def save_parent(self):
        pid_code = self.parent_id_code if self.is_edit else self.entry_pid.get().strip()
        name = self.entry_name.get().strip()
        sid = self.entry_sid.get().strip()
        phone = self.entry_phone.get().strip()
        email = self.entry_email.get().strip()

        if not pid_code or not name or not sid or not phone:
            messagebox.showwarning("Validation Error", "Parent ID, Name, Linked Student ID, and Phone are required.")
            return

        if not validate_phone(phone):
            messagebox.showwarning("Validation Error", "Phone number must contain exactly 10 digits.")
            return

        if email and not validate_email(email):
            messagebox.showwarning("Validation Error", "Please enter a valid Email Address.")
            return

        if not self.is_edit and self.db.is_parent_id_exists(pid_code):
            messagebox.showerror("Duplicate Error", f"Parent ID '{pid_code}' already exists in database.")
            return

        student = self.db.get_student(sid)
        if not student:
            messagebox.showerror("Validation Error", f"Linked Student ID '{sid}' was not found in database.\nPlease enter a valid Student ID.")
            return

        data = {
            "parent_id_code": pid_code,
            "name": name,
            "student_id": sid,
            "relationship": self.combo_relation.get(),
            "phone": phone,
            "email": email,
            "address": self.entry_address.get().strip()
        }

        if self.is_edit:
            ok = self.db.update_parent(pid_code, data)
        else:
            ok = self.db.add_parent(data)

        if ok:
            messagebox.showinfo("Success", f"Parent record {'updated' if self.is_edit else 'saved'} successfully.")
            self.destroy()
            if self.on_save:
                self.on_save()
        else:
            messagebox.showerror("Database Error", "Failed to save Parent record.")
