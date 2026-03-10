import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

THEME = {
    "primary":    "#F43F5E",
    "primary_dk": "#BE123C",
    "bg_page":    "#F1F5F9",
    "bg_card":    "#FFFFFF",
    "text_main":  "#0F172A",
    "text_muted": "#64748B",
    "border":     "#E2E8F0",
    "dark":       "#1E293B",
}

STATUS_OPTIONS = ["P - Present", "A - Absent", "PL - Paid Leave", "PP - Present with Permission"]
STATUS_LABELS  = {"P": "Present", "A": "Absent", "PL": "Paid Leave", "PP": "Present w/Permission"}
STATUS_COLORS  = {"P": "#D1FAE5", "A": "#FEE2E2", "PL": "#FEF3C7", "PP": "#E0E7FF"}
STATUS_ICONS   = {"P": "✅", "A": "❌", "PL": "🏖", "PP": "🕐"}


def _parse_code(combo_val):
    """Extract 'P', 'A', 'PL', 'PP' from combo string like 'P - Present'."""
    return combo_val.split(" - ")[0].strip()


class AttendanceView(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg=THEME["bg_page"])
        self.db = db
        self._build_ui()
        self._refresh_emp_list()
        self._load_table()

    # ─────────────────────── UI BUILD ────────────────────────────────────────
    def _build_ui(self):
        # ── ENTRY CARD ──
        entry_card = tk.Frame(self, bg=THEME["bg_card"], padx=28, pady=20)
        entry_card.pack(side="top", fill="x", pady=(0, 18))
        entry_card.config(highlightbackground=THEME["border"], highlightthickness=1)

        tk.Label(entry_card,
                 text="📋  Mark / Update Attendance",
                 font=("Segoe UI Variable Display", 15, "bold"),
                 bg=THEME["bg_card"], fg=THEME["text_main"]).pack(anchor="w", pady=(0, 14))

        fields_row = tk.Frame(entry_card, bg=THEME["bg_card"])
        fields_row.pack(fill="x")

        def _col(parent, lbl):
            f = tk.Frame(parent, bg=THEME["bg_card"])
            f.pack(side="left", padx=(0, 18), anchor="n")
            tk.Label(f, text=lbl, font=("Segoe UI Semibold", 8),
                     bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(anchor="w")
            return f

        # Employee dropdown
        f_emp = _col(fields_row, "SELECT EMPLOYEE")
        self.emp_cb = ttk.Combobox(f_emp, width=28, state="readonly",
                                    font=("Segoe UI", 10))
        self.emp_cb.pack(ipady=4, pady=(3, 0))

        # Date
        f_dt = _col(fields_row, "DATE  (YYYY-MM-DD)")
        self.date_ent = tk.Entry(f_dt, font=("Segoe UI", 11), width=14,
                                  bd=0, bg="#F8FAFC",
                                  highlightthickness=1,
                                  highlightbackground=THEME["border"])
        self.date_ent.pack(ipady=6, pady=(3, 0))
        self.date_ent.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Status
        f_st = _col(fields_row, "STATUS")
        self.status_cb = ttk.Combobox(
            f_st, values=STATUS_OPTIONS,
            width=26, state="readonly", font=("Segoe UI", 10))
        self.status_cb.pack(ipady=4, pady=(3, 0))
        self.status_cb.set(STATUS_OPTIONS[0])
        self.status_cb.bind("<<ComboboxSelected>>", self._toggle_perm)

        # Permission hours (visible only for PP)
        self.perm_frame = tk.Frame(fields_row, bg=THEME["bg_card"])
        tk.Label(self.perm_frame, text="PERMISSION HOURS",
                 font=("Segoe UI Semibold", 8),
                 bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(anchor="w")
        self.perm_ent = tk.Entry(self.perm_frame, font=("Segoe UI", 11),
                                  width=9, bd=0, bg="#F8FAFC",
                                  highlightthickness=1,
                                  highlightbackground=THEME["border"])
        self.perm_ent.pack(ipady=6, pady=(3, 0))
        self.perm_ent.insert(0, "0")

        # Save button
        tk.Button(fields_row, text="  💾  SAVE  ",
                  command=self._save_attendance,
                  bg=THEME["primary"], fg="white",
                  font=("Segoe UI Variable Text", 10, "bold"),
                  bd=0, padx=18, pady=10, cursor="hand2",
                  activebackground=THEME["primary_dk"]).pack(
            side="right", anchor="s", pady=(14, 0))

        # ── FILTER BAR ──
        fbar = tk.Frame(self, bg=THEME["bg_card"], padx=22, pady=12)
        fbar.pack(side="top", fill="x", pady=(0, 16))
        fbar.config(highlightbackground=THEME["border"], highlightthickness=1)

        tk.Label(fbar, text="Filter:",
                 font=("Segoe UI Semibold", 9),
                 bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(side="left")

        self.hist_emp_cb = ttk.Combobox(fbar, width=26, state="readonly")
        self.hist_emp_cb.pack(side="left", padx=8)

        tk.Label(fbar, text="Year:", bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 8), fg=THEME["text_muted"]).pack(side="left")
        self.year_cb = ttk.Combobox(
            fbar, values=[str(y) for y in range(2025, 2091)],
            width=7, state="readonly")
        self.year_cb.pack(side="left", padx=5)
        self.year_cb.set(datetime.now().strftime("%Y"))

        tk.Label(fbar, text="Month:", bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 8), fg=THEME["text_muted"]).pack(side="left")
        self.month_cb = ttk.Combobox(
            fbar, values=[f"{i:02d}" for i in range(1, 13)],
            width=5, state="readonly")
        self.month_cb.pack(side="left", padx=5)
        self.month_cb.set(datetime.now().strftime("%m"))

        tk.Button(fbar, text="🔍 View",
                  command=self._load_table,
                  bg=THEME["dark"], fg="white",
                  font=("Segoe UI", 9, "bold"),
                  bd=0, padx=14, pady=5, cursor="hand2").pack(side="left", padx=10)

        # Summary chips container
        self._summary_frame = tk.Frame(fbar, bg=THEME["bg_card"])
        self._summary_frame.pack(side="right")

        # ── TABLE ──
        tbl = tk.Frame(self, bg=THEME["bg_card"])
        tbl.pack(fill="both", expand=True)
        tbl.config(highlightbackground=THEME["border"], highlightthickness=1)

        cols   = ("ID", "Employee Name", "Date", "Status", "Perm Hours")
        widths = [55,   210,              120,    210,       100]
        self.tree = ttk.Treeview(tbl, columns=cols, show="headings")
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w")
        self.tree.column("ID",         anchor="center")
        self.tree.column("Perm Hours", anchor="center")
        self.tree.pack(fill="both", expand=True)

        for code, color in STATUS_COLORS.items():
            self.tree.tag_configure(code, background=color)

        sc = ttk.Scrollbar(tbl, orient="vertical", command=self.tree.yview)
        sc.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sc.set)

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    # ─────────────────────── HELPERS ─────────────────────────────────────────
    def _toggle_perm(self, _event=None):
        code = _parse_code(self.status_cb.get())
        if code == "PP":
            self.perm_frame.pack(side="left", padx=(0, 18), anchor="n")
        else:
            self.perm_frame.pack_forget()

    def _refresh_emp_list(self):
        conn = self.db.get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT emp_id, name FROM employees ORDER BY name")
        self._employees = cur.fetchall()
        conn.close()
        items = [f"{r['emp_id']} | {r['name']}" for r in self._employees]
        self.emp_cb["values"]      = items
        self.hist_emp_cb["values"] = ["ALL EMPLOYEES"] + items
        self.hist_emp_cb.set("ALL EMPLOYEES")

    # ─────────────────────── SAVE ────────────────────────────────────────────
    def _save_attendance(self):
        emp_sel = self.emp_cb.get()
        if not emp_sel:
            messagebox.showwarning("Required", "Please select an employee.")
            return

        emp_id = int(emp_sel.split(" | ")[0].strip())
        date   = self.date_ent.get().strip()

        # Validate date
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Date must be in YYYY-MM-DD format.\nExample: 2025-06-15")
            return

        code = _parse_code(self.status_cb.get())

        perm_hrs = 0.0
        if code == "PP":
            try:
                perm_hrs = float(self.perm_ent.get() or 0)
            except ValueError:
                messagebox.showerror("Invalid", "Permission hours must be a number.")
                return

        conn = self.db.get_connection()
        cur  = conn.cursor()

        # Check if record already exists for this emp+date
        cur.execute(
            "SELECT id FROM attendance WHERE emp_id=? AND date=?",
            (emp_id, date))
        existing = cur.fetchone()

        if existing:
            cur.execute(
                "UPDATE attendance SET status=?, permission_hours=? WHERE id=?",
                (code, perm_hrs, existing["id"]))
            msg = f"Updated attendance for {emp_sel}\n{date}  →  {STATUS_ICONS.get(code,'')} {STATUS_LABELS.get(code,code)}"
        else:
            cur.execute(
                "INSERT INTO attendance (emp_id, date, status, permission_hours) "
                "VALUES (?,?,?,?)",
                (emp_id, date, code, perm_hrs))
            msg = f"Saved attendance for {emp_sel}\n{date}  →  {STATUS_ICONS.get(code,'')} {STATUS_LABELS.get(code,code)}"

        conn.commit()
        conn.close()
        messagebox.showinfo("Saved ✔", msg)

        # Auto-update filter to show the month of the saved date
        saved_year  = date[:4]
        saved_month = date[5:7]
        self.year_cb.set(saved_year)
        self.month_cb.set(saved_month)
        self._load_table()

    # ─────────────────────── LOAD TABLE ──────────────────────────────────────
    def _load_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        year  = self.year_cb.get()
        month = self.month_cb.get()
        patt  = f"{year}-{month}%"
        emp_f = self.hist_emp_cb.get()

        conn = self.db.get_connection()
        cur  = conn.cursor()

        if emp_f == "ALL EMPLOYEES" or not emp_f:
            cur.execute(
                '''SELECT a.id, e.name, a.date, a.status, a.permission_hours
                   FROM attendance a
                   JOIN employees e ON a.emp_id = e.emp_id
                   WHERE a.date LIKE ?
                   ORDER BY a.date DESC, e.name''',
                (patt,))
        else:
            eid = int(emp_f.split(" | ")[0].strip())
            cur.execute(
                '''SELECT a.id, e.name, a.date, a.status, a.permission_hours
                   FROM attendance a
                   JOIN employees e ON a.emp_id = e.emp_id
                   WHERE a.emp_id=? AND a.date LIKE ?
                   ORDER BY a.date DESC''',
                (eid, patt))

        rows = cur.fetchall()
        conn.close()

        counts = {"P": 0, "A": 0, "PL": 0, "PP": 0}
        for r in rows:
            code = r["status"]
            counts[code] = counts.get(code, 0) + 1
            display = f"{STATUS_ICONS.get(code,'')} {STATUS_LABELS.get(code, code)}"
            perm    = r["permission_hours"] if r["permission_hours"] else "-"
            self.tree.insert("", "end",
                             values=(r["id"], r["name"], r["date"], display, perm),
                             tags=(code,))

        # Refresh summary chips
        for w in self._summary_frame.winfo_children():
            w.destroy()
        chip_bg = {"P": "#D1FAE5", "A": "#FEE2E2", "PL": "#FEF3C7", "PP": "#E0E7FF"}
        for code, cnt in counts.items():
            chip = tk.Frame(self._summary_frame, bg=chip_bg[code], padx=10, pady=4)
            chip.pack(side="left", padx=3)
            tk.Label(chip,
                     text=f"{STATUS_ICONS[code]} {STATUS_LABELS[code]}: {cnt}",
                     font=("Segoe UI Semibold", 8),
                     bg=chip_bg[code], fg=THEME["text_main"]).pack()

    # ─────────────────────── ROW SELECT ──────────────────────────────────────
    def _on_row_select(self, _event):
        """Clicking a row pre-fills date + status for quick editing."""
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])["values"]
        # vals: (ID, Name, Date, StatusDisplay, PermHrs)
        date_val   = str(vals[2])
        status_disp = str(vals[3])   # e.g. "✅ Present"

        self.date_ent.delete(0, "end")
        self.date_ent.insert(0, date_val)

        # Reverse-map display text to combo option
        rev_map = {
            "Present":           "P - Present",
            "Absent":            "A - Absent",
            "Paid Leave":        "PL - Paid Leave",
            "Present w/Permission": "PP - Present with Permission",
        }
        for key, opt in rev_map.items():
            if key in status_disp:
                self.status_cb.set(opt)
                self._toggle_perm()
                break

        # Set perm hours if shown
        if str(vals[4]) != "-":
            self.perm_ent.delete(0, "end")
            self.perm_ent.insert(0, str(vals[4]))
