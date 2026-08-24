import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS
from utils.validators import validate_email, validate_phone

class TeacherFormDialog(tk.Toplevel):
    """Dialog for Admin to Add or Edit Teacher details."""
    def __init__(self, parent_win, db_manager: DBManager, teacher_id: str = None, on_save_callback=None):
        super().__init__(parent_win)
        self.db = db_manager
        self.teacher_id = teacher_id
        self.is_edit = teacher_id is not None
        self.on_save = on_save_callback

        self.title("Edit Teacher" if self.is_edit else "Add New Teacher")
        self.geometry("500x580")
        self.resizable(False, False)
        self.transient(parent_win)
        self.grab_set()

        self._build_ui()
        if self.is_edit:
            self._load_teacher_data()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_text = "✏️ Edit Teacher Record" if self.is_edit else "➕ Add New Teacher"
        ttk.Label(main_frame, text=title_text, font=FONTS["h2"]).pack(anchor=tk.W, pady=(0, 15))

        f = ttk.Frame(main_frame)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="Teacher ID *:", font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", pady=6)
        self.entry_tid = ttk.Entry(f, width=30)
        self.entry_tid.grid(row=0, column=1, sticky="w", pady=6, padx=10)
        if self.is_edit:
            self.entry_tid.config(state="disabled")

        ttk.Label(f, text="Full Name *:", font=FONTS["body_bold"]).grid(row=1, column=0, sticky="w", pady=6)
        self.entry_name = ttk.Entry(f, width=30)
        self.entry_name.grid(row=1, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Phone Number *:", font=FONTS["body_bold"]).grid(row=2, column=0, sticky="w", pady=6)
        self.entry_phone = ttk.Entry(f, width=30)
        self.entry_phone.grid(row=2, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Email Address:", font=FONTS["body_bold"]).grid(row=3, column=0, sticky="w", pady=6)
        self.entry_email = ttk.Entry(f, width=30)
        self.entry_email.grid(row=3, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Department *:", font=FONTS["body_bold"]).grid(row=4, column=0, sticky="w", pady=6)
        self.entry_dept = ttk.Entry(f, width=30)
        self.entry_dept.insert(0, "Computer Science & Engineering")
        self.entry_dept.grid(row=4, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Designation:", font=FONTS["body_bold"]).grid(row=5, column=0, sticky="w", pady=6)
        self.entry_desig = ttk.Entry(f, width=30)
        self.entry_desig.insert(0, "Assistant Professor")
        self.entry_desig.grid(row=5, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Joining Date:", font=FONTS["body_bold"]).grid(row=6, column=0, sticky="w", pady=6)
        self.entry_joining = ttk.Entry(f, width=30)
        self.entry_joining.insert(0, "2024-01-15")
        self.entry_joining.grid(row=6, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Address:", font=FONTS["body_bold"]).grid(row=7, column=0, sticky="w", pady=6)
        self.entry_address = ttk.Entry(f, width=30)
        self.entry_address.grid(row=7, column=1, sticky="w", pady=6, padx=10)

        btn_bar = ttk.Frame(main_frame)
        btn_bar.pack(fill=tk.X, pady=(20, 0))

        btn_save = ttk.Button(btn_bar, text="💾 Save Record", style="Primary.TButton", command=self.save_teacher)
        btn_save.pack(side=tk.RIGHT, padx=5)

        btn_cancel = ttk.Button(btn_bar, text="Cancel", command=self.destroy)
        btn_cancel.pack(side=tk.RIGHT, padx=5)

    def _load_teacher_data(self):
        t = self.db.get_teacher(self.teacher_id)
        if not t:
            return

        self.entry_tid.config(state="normal")
        self.entry_tid.delete(0, tk.END)
        self.entry_tid.insert(0, t.get('teacher_id', ''))
        self.entry_tid.config(state="disabled")

        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, t.get('name', ''))

        self.entry_phone.delete(0, tk.END)
        self.entry_phone.insert(0, t.get('phone', ''))

        self.entry_email.delete(0, tk.END)
        self.entry_email.insert(0, t.get('email', ''))

        self.entry_dept.delete(0, tk.END)
        self.entry_dept.insert(0, t.get('department', 'Computer Science & Engineering'))

        self.entry_desig.delete(0, tk.END)
        self.entry_desig.insert(0, t.get('designation', 'Assistant Professor'))

        self.entry_joining.delete(0, tk.END)
        self.entry_joining.insert(0, t.get('joining_date', '2024-01-15'))

        self.entry_address.delete(0, tk.END)
        self.entry_address.insert(0, t.get('address', ''))

    def save_teacher(self):
        tid = self.teacher_id if self.is_edit else self.entry_tid.get().strip()
        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        email = self.entry_email.get().strip()

        if not tid or not name or not phone:
            messagebox.showwarning("Validation Error", "Teacher ID, Full Name, and Phone Number are required.")
            return

        if not validate_phone(phone):
            messagebox.showwarning("Validation Error", "Phone number must contain exactly 10 digits.")
            return

        if email and not validate_email(email):
            messagebox.showwarning("Validation Error", "Please enter a valid Email Address.")
            return

        if not self.is_edit and self.db.is_teacher_id_exists(tid):
            messagebox.showerror("Duplicate Error", f"Teacher ID '{tid}' already exists in database.")
            return

        data = {
            "teacher_id": tid,
            "name": name,
            "phone": phone,
            "email": email,
            "department": self.entry_dept.get().strip(),
            "designation": self.entry_desig.get().strip(),
            "joining_date": self.entry_joining.get().strip(),
            "address": self.entry_address.get().strip()
        }

        if self.is_edit:
            ok = self.db.update_teacher(tid, data)
        else:
            ok = self.db.add_teacher(data)

        if ok:
            messagebox.showinfo("Success", f"Teacher record {'updated' if self.is_edit else 'saved'} successfully.")
            self.destroy()
            if self.on_save:
                self.on_save()
        else:
            messagebox.showerror("Database Error", "Failed to save Teacher record.")
