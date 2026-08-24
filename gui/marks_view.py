import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS
from utils.validators import validate_marks
from utils.helpers import calculate_grade_and_status

class MarksEntryDialog(tk.Toplevel):
    """Modal dialog for subject-wise academic marks management & overall summary."""
    def __init__(self, parent, db_manager: DBManager, student_id: str, student_name: str, subject: str = "Mathematics", on_save_callback=None):
        super().__init__(parent)
        self.db = db_manager
        self.student_id = student_id
        self.student_name = student_name
        self.subject = subject
        self.on_save = on_save_callback
        self.editing_subject = None

        self.title(f"Academic Marks Management - {student_name} ({student_id})")
        self.geometry("780x680")
        self.minsize(720, 600)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._load_subject_marks_table()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Header Section
        ttk.Label(main_frame, text="📊 Subject-Wise Academic Marks Management", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 2))
        ttk.Label(main_frame, text=f"Student: {self.student_name} | ID: {self.student_id}", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        # 2. Form Section for Subject Entry
        form_box = ttk.LabelFrame(main_frame, text=" Add / Edit Subject Marks ", padding=10)
        form_box.pack(fill=tk.X, pady=(0, 10))

        # Subject Name Entry (Free-form text input)
        subj_frame = ttk.Frame(form_box)
        subj_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(subj_frame, text="Subject Name *:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_subject = ttk.Entry(subj_frame, width=35)
        self.entry_subject.insert(0, self.subject)
        self.entry_subject.pack(side=tk.LEFT, padx=5)

        # Marks Grid Inputs
        grid_frame = ttk.Frame(form_box)
        grid_frame.pack(fill=tk.X, pady=4)

        ttk.Label(grid_frame, text="Internal (Max 20):", font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.entry_internal = ttk.Entry(grid_frame, width=10)
        self.entry_internal.insert(0, "0.0")
        self.entry_internal.grid(row=0, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(grid_frame, text="Mid-Term (Max 30):", font=FONTS["body_bold"]).grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.entry_mid = ttk.Entry(grid_frame, width=10)
        self.entry_mid.insert(0, "0.0")
        self.entry_mid.grid(row=0, column=3, sticky="w", padx=5, pady=4)

        ttk.Label(grid_frame, text="Project (Max 20):", font=FONTS["body_bold"]).grid(row=0, column=4, sticky="w", padx=5, pady=4)
        self.entry_proj = ttk.Entry(grid_frame, width=10)
        self.entry_proj.insert(0, "0.0")
        self.entry_proj.grid(row=0, column=5, sticky="w", padx=5, pady=4)

        ttk.Label(grid_frame, text="Viva (Max 10):", font=FONTS["body_bold"]).grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.entry_viva = ttk.Entry(grid_frame, width=10)
        self.entry_viva.insert(0, "0.0")
        self.entry_viva.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(grid_frame, text="Final Exam (Max 100):", font=FONTS["body_bold"]).grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.entry_final = ttk.Entry(grid_frame, width=10)
        self.entry_final.insert(0, "0.0")
        self.entry_final.grid(row=1, column=3, sticky="w", padx=5, pady=4)

        # Action Buttons for Form
        btn_form_frame = ttk.Frame(grid_frame)
        btn_form_frame.grid(row=1, column=4, columnspan=2, sticky="e", padx=5, pady=4)

        ttk.Button(btn_form_frame, text="➕ Add Subject", style="Accent.TButton", command=self._add_new_subject_form).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_form_frame, text="💾 Save Subject Marks", style="Primary.TButton", command=self.save_marks).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_form_frame, text="🧹 Clear", command=self._clear_form).pack(side=tk.LEFT, padx=3)

        # Subject Live Preview Label
        self.lbl_preview = ttk.Label(form_box, text="Subject Total: 0.0 / 180.0 | Pct: 0.0% | Grade: F | Status: Fail", font=FONTS["body_bold"], foreground=COLORS["primary"])
        self.lbl_preview.pack(anchor=tk.W, pady=(5, 2))

        for entry in [self.entry_internal, self.entry_mid, self.entry_proj, self.entry_viva, self.entry_final]:
            entry.bind("<KeyRelease>", self._update_preview)

        # 3. Subject-Wise Table Section
        table_box = ttk.LabelFrame(main_frame, text=" SUBJECT-WISE MARKS RECORDS ", padding=10)
        table_box.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tbl_frame = ttk.Frame(table_box)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("subject", "internal", "mid", "proj", "viva", "final", "total", "pct", "grade", "status")
        self.tree_marks = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=6)

        self.tree_marks.heading("subject", text="Subject Name")
        self.tree_marks.heading("internal", text="Internal")
        self.tree_marks.heading("mid", text="Mid-Term")
        self.tree_marks.heading("proj", text="Project")
        self.tree_marks.heading("viva", text="Viva")
        self.tree_marks.heading("final", text="Final Exam")
        self.tree_marks.heading("total", text="Total")
        self.tree_marks.heading("pct", text="Pct %")
        self.tree_marks.heading("grade", text="Grade")
        self.tree_marks.heading("status", text="Status")

        self.tree_marks.column("subject", width=160, anchor="w")
        self.tree_marks.column("internal", width=65, anchor="center")
        self.tree_marks.column("mid", width=65, anchor="center")
        self.tree_marks.column("proj", width=65, anchor="center")
        self.tree_marks.column("viva", width=60, anchor="center")
        self.tree_marks.column("final", width=75, anchor="center")
        self.tree_marks.column("total", width=65, anchor="center")
        self.tree_marks.column("pct", width=65, anchor="center")
        self.tree_marks.column("grade", width=60, anchor="center")
        self.tree_marks.column("status", width=70, anchor="center")

        scrollbar = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree_marks.yview)
        self.tree_marks.configure(yscroll=scrollbar.set)
        self.tree_marks.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Table Action Buttons
        tbl_act_frame = ttk.Frame(table_box)
        tbl_act_frame.pack(fill=tk.X, pady=(6, 0))

        ttk.Button(tbl_act_frame, text="✏️ Edit Selected Subject", command=self.edit_selected_subject).pack(side=tk.LEFT, padx=3)
        ttk.Button(tbl_act_frame, text="🗑️ Delete Selected Subject", style="Danger.TButton", command=self.delete_selected_subject).pack(side=tk.RIGHT, padx=3)

        # 4. Overall Result Summary Section
        summary_box = ttk.LabelFrame(main_frame, text=" OVERALL RESULT SUMMARY ", padding=10)
        summary_box.pack(fill=tk.X, pady=(0, 5))

        self.lbl_overall = ttk.Label(
            summary_box,
            text="Total Subjects: 0 | Marks Obtained: 0.0 / 0.0 | Overall Percentage: 0.0% | Result: PASS",
            font=FONTS["h3"],
            foreground=COLORS["primary"]
        )
        self.lbl_overall.pack(anchor=tk.W)

    def _add_new_subject_form(self):
        """Prepare a fresh blank subject-entry form without clearing saved database subjects."""
        self.entry_subject.delete(0, tk.END)
        for entry in [self.entry_internal, self.entry_mid, self.entry_proj, self.entry_viva, self.entry_final]:
            entry.delete(0, tk.END)
            entry.insert(0, "0.0")
        self.editing_subject = None
        self._update_preview()
        self.entry_subject.focus_set()

    def _update_preview(self, event=None):
        try:
            val_int = float(self.entry_internal.get() or 0)
            val_mid = float(self.entry_mid.get() or 0)
            val_proj = float(self.entry_proj.get() or 0)
            val_viva = float(self.entry_viva.get() or 0)
            val_final = float(self.entry_final.get() or 0)

            total = val_int + val_mid + val_proj + val_viva + val_final
            pct, grade, status = calculate_grade_and_status(total)

            color = COLORS["success"] if status == "Pass" else COLORS["danger"]
            self.lbl_preview.config(
                text=f"Subject Total: {total:.1f} / 180.0 | Pct: {pct:.1f}% | Grade: {grade} | Status: {status}",
                foreground=color
            )
        except ValueError:
            self.lbl_preview.config(text="Enter valid numeric marks...", foreground=COLORS["warning"])

    def _clear_form(self):
        self._add_new_subject_form()

    def _load_subject_marks_table(self):
        for item in self.tree_marks.get_children():
            self.tree_marks.delete(item)

        records = self.db.get_all_student_marks(self.student_id)

        total_subjects = len(records)
        total_obtained_100 = 0.0
        total_max_100 = total_subjects * 100.0
        any_failed = False

        for r in records:
            subj = r.get('subject', '')
            val_int = float(r.get('internal_marks', 0.0))
            val_mid = float(r.get('mid_term_marks', 0.0))
            val_proj = float(r.get('project_marks', 0.0))
            val_viva = float(r.get('viva_marks', 0.0))
            val_final = float(r.get('final_exam_marks', 0.0))
            stotal = float(r.get('total_marks', val_int + val_mid + val_proj + val_viva + val_final))

            # Calculate subject score out of 100
            # If percentage is stored, use it; otherwise compute from stotal / 180.0 * 100.0 or raw stotal if <= 100
            if 'percentage' in r and r['percentage'] is not None and r['percentage'] > 0:
                subj_score = float(r['percentage'])
            else:
                subj_score = round((stotal / 180.0 * 100.0), 2) if stotal <= 180.0 else min(100.0, stotal)

            grade = r.get('grade', 'F')
            status = r.get('status', 'Fail')

            if status.lower() == 'fail':
                any_failed = True
            total_obtained_100 += subj_score

            self.tree_marks.insert("", tk.END, values=(
                subj, val_int, val_mid, val_proj, val_viva, val_final,
                f"{stotal:g}", f"{subj_score:.1f}%", grade, status
            ))

        # Dynamic Overall Summary Calculation (Total Subjects * 100)
        overall_pct = round((total_obtained_100 / total_max_100 * 100.0), 2) if total_max_100 > 0 else 0.0
        overall_result = "FAIL" if (any_failed or overall_pct < 40.0) else "PASS"
        res_color = COLORS["success"] if overall_result == "PASS" else COLORS["danger"]

        self.lbl_overall.config(
            text=f"Total Subjects: {total_subjects}  |  Marks Obtained: {total_obtained_100:g} / {total_max_100:g}  |  Overall Percentage: {overall_pct:.2f}%  |  Result: {overall_result}",
            foreground=res_color
        )

    def edit_selected_subject(self):
        sel = self.tree_marks.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a subject from the table to edit.")
            return

        row_vals = self.tree_marks.item(sel[0])['values']
        subj_name = str(row_vals[0])

        m = self.db.get_student_marks(self.student_id, subj_name)
        if not m:
            messagebox.showerror("Error", f"Could not load marks for '{subj_name}'.")
            return

        self.editing_subject = subj_name
        self.entry_subject.delete(0, tk.END)
        self.entry_subject.insert(0, subj_name)

        self.entry_internal.delete(0, tk.END)
        self.entry_internal.insert(0, str(m.get('internal_marks', 0.0)))

        self.entry_mid.delete(0, tk.END)
        self.entry_mid.insert(0, str(m.get('mid_term_marks', 0.0)))

        self.entry_proj.delete(0, tk.END)
        self.entry_proj.insert(0, str(m.get('project_marks', 0.0)))

        self.entry_viva.delete(0, tk.END)
        self.entry_viva.insert(0, str(m.get('viva_marks', 0.0)))

        self.entry_final.delete(0, tk.END)
        self.entry_final.insert(0, str(m.get('final_exam_marks', 0.0)))

        self._update_preview()

    def delete_selected_subject(self):
        sel = self.tree_marks.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a subject from the table to delete.")
            return

        subj_name = str(self.tree_marks.item(sel[0])['values'][0])
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete marks record for subject '{subj_name}'?\nThis action cannot be undone."):
            self.db.delete_student_marks(self.student_id, subj_name)
            messagebox.showinfo("Deleted", f"Marks record for '{subj_name}' deleted.")
            self._load_subject_marks_table()
            if self.on_save:
                self.on_save()

    def save_marks(self):
        subj = self.entry_subject.get().strip()
        if not subj:
            messagebox.showwarning("Validation Error", "Subject Name is required.")
            return

        valid, msg = validate_marks(
            self.entry_internal.get(),
            self.entry_mid.get(),
            self.entry_proj.get(),
            self.entry_viva.get(),
            self.entry_final.get()
        )

        if not valid:
            messagebox.showerror("Invalid Marks", msg)
            return

        # If user renamed subject while editing, remove old subject entry safely
        if self.editing_subject and self.editing_subject.lower() != subj.lower():
            self.db.delete_student_marks(self.student_id, self.editing_subject)

        marks_data = {
            'internal_marks': float(self.entry_internal.get()),
            'mid_term_marks': float(self.entry_mid.get()),
            'project_marks': float(self.entry_proj.get()),
            'viva_marks': float(self.entry_viva.get()),
            'final_exam_marks': float(self.entry_final.get())
        }

        saved_ok = self.db.save_or_update_marks(self.student_id, marks_data, subj)
        if not saved_ok:
            messagebox.showerror("Database Error", f"Failed to save marks for subject '{subj}'.")
            return

        self.editing_subject = None

        # Reload records table directly from database so table updates IMMEDIATELY
        self._load_subject_marks_table()

        # Show success message AFTER database table has refreshed with latest data
        messagebox.showinfo("Success", f"Marks for subject '{subj}' saved successfully!")

        if self.on_save:
            self.on_save()
