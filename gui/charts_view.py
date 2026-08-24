import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from database.db_manager import DBManager

class AnalyticsChartsFrame(ttk.Frame):
    """Integrates Matplotlib visual charts directly into Tkinter dashboards."""
    def __init__(self, parent, db_manager: DBManager, student_id: str = None):
        super().__init__(parent, padding=10)
        self.db = db_manager
        self.student_id = student_id

        self._build_ui()
        self.plot_all_charts()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def plot_all_charts(self):
        for widget in self.winfo_children():
            widget.destroy()

        if self.student_id:
            self._plot_student_charts()
        else:
            self._plot_system_charts()

    def _plot_student_charts(self):
        # 1. Student Attendance Pie Chart
        att_stats = self.db.get_student_attendance_stats(self.student_id)
        p_days = att_stats['present_days']
        a_days = att_stats['absent_days']

        fig1, ax1 = plt.subplots(figsize=(4.2, 3.2), dpi=100)
        fig1.patch.set_facecolor('#ffffff')
        
        if p_days == 0 and a_days == 0:
            ax1.text(0.5, 0.5, 'No Attendance Data Recorded', horizontalalignment='center', verticalalignment='center', transform=ax1.transAxes)
            ax1.axis('off')
        else:
            labels = ['Present', 'Absent']
            sizes = [p_days, a_days]
            colors = ['#16a34a', '#dc2626']
            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 9})
            ax1.set_title('Attendance Ratio', fontsize=11, fontweight='bold')

        canvas1 = FigureCanvasTkAgg(fig1, master=self)
        canvas1.draw()
        canvas1.get_tk_widget().grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        # 2. Student Subject Marks Bar Chart
        marks = self.db.get_student_marks(self.student_id)
        fig2, ax2 = plt.subplots(figsize=(4.8, 3.2), dpi=100)
        fig2.patch.set_facecolor('#ffffff')

        if not marks:
            ax2.text(0.5, 0.5, 'No Academic Marks Recorded', horizontalalignment='center', verticalalignment='center', transform=ax2.transAxes)
            ax2.axis('off')
        else:
            categories = ['Internal\n(Max 20)', 'Mid-Term\n(Max 30)', 'Project\n(Max 20)', 'Viva\n(Max 10)', 'Final Exam\n(Max 100)']
            vals = [
                marks.get('internal_marks', 0),
                marks.get('mid_term_marks', 0),
                marks.get('project_marks', 0),
                marks.get('viva_marks', 0),
                marks.get('final_exam_marks', 0)
            ]
            max_vals = [20, 30, 20, 10, 100]
            pcts = [(v / m * 100) if m > 0 else 0 for v, m in zip(vals, max_vals)]

            bars = ax2.bar(categories, pcts, color=['#2563eb', '#0d9488', '#7c3aed', '#d97706', '#059669'])
            ax2.set_ylabel('Score (%)', fontsize=9)
            ax2.set_ylim(0, 105)
            ax2.set_title('Marks Breakdown (% Score)', fontsize=11, fontweight='bold')
            ax2.tick_params(axis='x', labelsize=8)

            for bar, val in zip(bars, vals):
                yval = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f"{val:.0f}", ha='center', va='bottom', fontsize=8)

        canvas2 = FigureCanvasTkAgg(fig2, master=self)
        canvas2.draw()
        canvas2.get_tk_widget().grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

    def _plot_system_charts(self):
        # 1. System Overall Attendance Chart
        summary = self.db.get_dashboard_summary()
        p = summary['today_present']
        a = summary['today_absent']

        fig1, ax1 = plt.subplots(figsize=(4.2, 3.2), dpi=100)
        fig1.patch.set_facecolor('#ffffff')

        if p == 0 and a == 0:
            ax1.pie([1], labels=['No Data Today'], colors=['#cbd5e1'], autopct='')
            ax1.set_title("Today's Attendance Status", fontsize=11, fontweight='bold')
        else:
            ax1.pie([p, a], labels=['Present', 'Absent'], colors=['#16a34a', '#dc2626'], autopct='%1.1f%%', startangle=90)
            ax1.set_title("Today's Attendance Distribution", fontsize=11, fontweight='bold')

        canvas1 = FigureCanvasTkAgg(fig1, master=self)
        canvas1.draw()
        canvas1.get_tk_widget().grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        # 2. Performance Grade Distribution
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT grade, COUNT(*) as count FROM marks GROUP BY grade")
            rows = cursor.fetchall()
            grade_counts = {r['grade']: r['count'] for r in rows}

        fig2, ax2 = plt.subplots(figsize=(4.8, 3.2), dpi=100)
        fig2.patch.set_facecolor('#ffffff')

        grades = ['A+', 'A', 'B+', 'B', 'C', 'D', 'F']
        counts = [grade_counts.get(g, 0) for g in grades]

        bars = ax2.bar(grades, counts, color='#2563eb')
        ax2.set_xlabel('Grade Letter', fontsize=9)
        ax2.set_ylabel('Number of Students', fontsize=9)
        ax2.set_title('Academic Grade Distribution', fontsize=11, fontweight='bold')
        
        for bar in bars:
            yval = bar.get_height()
            if yval > 0:
                ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, f"{int(yval)}", ha='center', va='bottom', fontsize=8)

        canvas2 = FigureCanvasTkAgg(fig2, master=self)
        canvas2.draw()
        canvas2.get_tk_widget().grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
