import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

THEME = {
    "primary":    "#F43F5E",
    "primary_dk": "#BE123C",
    "secondary":  "#6366F1",
    "bg_page":    "#F1F5F9",
    "bg_card":    "#FFFFFF",
    "text_main":  "#0F172A",
    "text_muted": "#64748B",
    "border":     "#E2E8F0",
    "success":    "#10B981",
    "dark":       "#1E293B",
}

DENOMS = [2, 5, 10, 20, 50, 100, 200, 500]
DENOM_COLS = {2: "c2", 5: "c5", 10: "c10", 20: "c20",
              50: "c50", 100: "c100", 200: "c200", 500: "c500"}


class MoneyView(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg=THEME["bg_page"])
        self.db = db
        self._build_ui()
        self._load_history()

    # ─────────────────────── UI BUILD ────────────────────────────────────────
    def _build_ui(self):
        # ── LEFT: entry form ──
        left = tk.Frame(self, bg=THEME["bg_page"], width=440)
        left.pack(side="left", fill="y", padx=(0, 28))
        left.pack_propagate(False)

        card = tk.Frame(left, bg=THEME["bg_card"], padx=28, pady=22)
        card.pack(fill="both", expand=True)
        card.config(highlightbackground=THEME["border"], highlightthickness=1)

        tk.Label(card, text="🏧  Vault Registry",
                 font=("Segoe UI Variable Display", 15, "bold"),
                 bg=THEME["bg_card"], fg=THEME["text_main"]).pack(anchor="w", pady=(0, 14))

        # ── Date field with Load button ──
        tk.Label(card, text="ACCOUNTING DATE  (YYYY-MM-DD)",
                 font=("Segoe UI Semibold", 8),
                 bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(anchor="w")
        date_row = tk.Frame(card, bg=THEME["bg_card"])
        date_row.pack(fill="x", pady=(4, 0))
        self.date_ent = tk.Entry(
            date_row, font=("Segoe UI", 11), bd=0, bg="#F8FAFC",
            highlightthickness=1, highlightbackground=THEME["border"])
        self.date_ent.pack(side="left", fill="x", expand=True,
                            padx=(0, 8), ipady=7)
        self.date_ent.insert(0, datetime.now().strftime("%Y-%m-%d"))
        tk.Button(date_row, text="📂 Load",
                  command=self._load_by_date,
                  bg=THEME["secondary"], fg="white",
                  font=("Segoe UI", 9, "bold"),
                  bd=0, padx=12, pady=7, cursor="hand2").pack(side="left")
        tk.Frame(card, bg=THEME["border"], height=1).pack(fill="x", pady=(6, 12))

        # ── Denomination grid ──
        tk.Label(card, text="CASH DENOMINATION COUNT",
                 font=("Segoe UI Semibold", 8),
                 bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(anchor="w")

        grid = tk.Frame(card, bg=THEME["bg_card"])
        grid.pack(fill="x", pady=(6, 10))
        self._denom_entries = {}
        for i, d in enumerate(DENOMS):
            r, c = divmod(i, 2)
            cell = tk.Frame(grid, bg="#F8FAFC",
                            highlightthickness=1,
                            highlightbackground=THEME["border"])
            cell.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)
            tk.Label(cell, text=f"₹{d}",
                     font=("Segoe UI Semibold", 9),
                     bg="#F8FAFC", fg=THEME["text_muted"]).pack(side="left", padx=8)
            ent = tk.Entry(cell, width=8,
                           font=("Segoe UI", 11, "bold"),
                           bd=0, bg="#F8FAFC", justify="right")
            ent.pack(side="right", padx=8, ipady=6)
            ent.insert(0, "0")
            ent.bind("<KeyRelease>", lambda _e: self._auto_calc())
            self._denom_entries[d] = ent
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        # Cash sub-total display
        self.cash_lbl = tk.Label(card, text="💵  Cash Total: ₹0.00",
                                  font=("Segoe UI Semibold", 10),
                                  bg=THEME["bg_card"], fg=THEME["text_main"])
        self.cash_lbl.pack(anchor="w", pady=(2, 0))

        # ── UPI field ──
        tk.Label(card, text="🔷  UPI / ONLINE PAYMENT (₹)",
                 font=("Segoe UI Semibold", 8),
                 bg=THEME["bg_card"], fg=THEME["secondary"]).pack(anchor="w", pady=(12, 0))
        upi_f = tk.Frame(card, bg="#EEF2FF",
                         highlightthickness=1,
                         highlightbackground=THEME["secondary"])
        upi_f.pack(fill="x", pady=(4, 0))
        self.upi_ent = tk.Entry(upi_f, font=("Segoe UI", 13, "bold"),
                                 bd=0, bg="#EEF2FF",
                                 fg=THEME["secondary"], justify="center")
        self.upi_ent.pack(fill="x", ipady=9)
        self.upi_ent.insert(0, "0")
        self.upi_ent.bind("<KeyRelease>", lambda _e: self._auto_calc())

        tk.Frame(card, bg=THEME["border"], height=1).pack(fill="x", pady=(10, 8))

        # Live summary
        self.summary_lbl = tk.Label(
            card, text="",
            font=("Segoe UI Variable Display", 11, "bold"),
            bg=THEME["bg_card"], fg=THEME["primary"],
            wraplength=360, justify="left")
        self.summary_lbl.pack(anchor="w", pady=(0, 10))

        # ── Buttons ──
        tk.Button(card, text="💾  SAVE / UPDATE RECORD",
                  command=self._save_record,
                  bg=THEME["primary"], fg="white",
                  font=("Segoe UI Variable Text", 11, "bold"),
                  bd=0, pady=12, cursor="hand2",
                  activebackground=THEME["primary_dk"]).pack(fill="x")
        tk.Button(card, text="✖  Clear Form",
                  command=self._clear_form,
                  bg="#F8FAFC", fg=THEME["text_muted"],
                  font=("Segoe UI", 9), bd=0, pady=6,
                  cursor="hand2").pack(fill="x", pady=(5, 0))

        # ── RIGHT: history table ──
        right = tk.Frame(self, bg=THEME["bg_card"])
        right.pack(side="right", fill="both", expand=True)
        right.config(highlightbackground=THEME["border"], highlightthickness=1)

        # Filter bar
        fbar = tk.Frame(right, bg="#F8FAFC", pady=12, padx=18)
        fbar.pack(side="top", fill="x")
        tk.Label(fbar, text="View by Month:",
                 font=("Segoe UI Semibold", 9),
                 bg="#F8FAFC", fg=THEME["text_muted"]).pack(side="left")
        self.f_year_cb = ttk.Combobox(
            fbar, values=[str(y) for y in range(2025, 2091)],
            width=7, state="readonly")
        self.f_year_cb.pack(side="left", padx=6)
        self.f_year_cb.set(datetime.now().strftime("%Y"))
        self.f_month_cb = ttk.Combobox(
            fbar, values=[f"{i:02d}" for i in range(1, 13)],
            width=5, state="readonly")
        self.f_month_cb.pack(side="left", padx=4)
        self.f_month_cb.set(datetime.now().strftime("%m"))
        tk.Button(fbar, text="🔍 Filter",
                  command=self._load_history,
                  bg=THEME["dark"], fg="white",
                  font=("Segoe UI", 9, "bold"), bd=0,
                  padx=14, pady=5, cursor="hand2").pack(side="left", padx=10)

        self.month_total_lbl = tk.Label(
            fbar, text="",
            font=("Segoe UI Semibold", 9),
            bg="#F8FAFC", fg=THEME["success"])
        self.month_total_lbl.pack(side="right")

        # Table (scrollable horizontally too)
        tbl_wrap = tk.Frame(right, bg=THEME["bg_card"])
        tbl_wrap.pack(fill="both", expand=True)

        cols = ("Date",
                "₹2", "₹5", "₹10", "₹20", "₹50",
                "₹100", "₹200", "₹500",
                "Cash Total", "UPI", "Gross Total", "Expenses", "Net")
        widths = {"Date": 100,
                  "₹2": 45, "₹5": 45, "₹10": 48, "₹20": 50, "₹50": 52,
                  "₹100": 55, "₹200": 58, "₹500": 58,
                  "Cash Total": 88, "UPI": 80,
                  "Gross Total": 90, "Expenses": 85, "Net": 90}

        self.tree = ttk.Treeview(tbl_wrap, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths.get(col, 70), anchor="center")
        self.tree.column("Date", anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        xsc = ttk.Scrollbar(tbl_wrap, orient="horizontal", command=self.tree.xview)
        xsc.pack(side="bottom", fill="x")
        ysc = ttk.Scrollbar(tbl_wrap, orient="vertical", command=self.tree.yview)
        ysc.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=ysc.set, xscrollcommand=xsc.set)

    # ─────────────────────── HELPERS ─────────────────────────────────────────
    def _get_denom_counts(self):
        counts = {}
        for d in DENOMS:
            raw = self._denom_entries[d].get().strip()
            counts[d] = int(raw) if raw.isdigit() else 0
        return counts

    def _get_upi(self):
        raw = self.upi_ent.get().strip()
        try:
            return float(raw)
        except ValueError:
            return 0.0

    def _auto_calc(self):
        counts    = self._get_denom_counts()
        cash_tot  = sum(d * counts[d] for d in DENOMS)
        upi       = self._get_upi()
        gross     = cash_tot + upi
        self.cash_lbl.config(text=f"💵  Cash Total: ₹{cash_tot:,.2f}")
        self.summary_lbl.config(
            text=f"Gross = Cash ₹{cash_tot:,.2f} + UPI ₹{upi:,.2f} = ₹{gross:,.2f}")

    def _clear_form(self):
        self.date_ent.delete(0, "end")
        self.date_ent.insert(0, datetime.now().strftime("%Y-%m-%d"))
        for ent in self._denom_entries.values():
            ent.delete(0, "end")
            ent.insert(0, "0")
        self.upi_ent.delete(0, "end")
        self.upi_ent.insert(0, "0")
        self.cash_lbl.config(text="💵  Cash Total: ₹0.00")
        self.summary_lbl.config(text="")

    def _load_by_date(self):
        """Load existing record for the entered date into the form."""
        date = self.date_ent.get().strip()
        if not date:
            messagebox.showwarning("Required", "Please enter a date.")
            return

        conn = self.db.get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM cash_records WHERE date=?", (date,))
        row = cur.fetchone()
        conn.close()

        if not row:
            # No record yet – just clear the denomination fields so user can enter fresh
            for ent in self._denom_entries.values():
                ent.delete(0, "end")
                ent.insert(0, "0")
            self.upi_ent.delete(0, "end")
            self.upi_ent.insert(0, "0")
            self.summary_lbl.config(text=f"No record for {date}. Enter values and Save.")
            return

        # Fill denomination entries using dict-style or index fallback
        for d, col in DENOM_COLS.items():
            val = self._safe_get(row, col, 0)
            self._denom_entries[d].delete(0, "end")
            self._denom_entries[d].insert(0, str(int(val)))

        upi_val = self._safe_get(row, "upi_amount", 0)
        self.upi_ent.delete(0, "end")
        self.upi_ent.insert(0, str(upi_val))
        self._auto_calc()

        # Update the history table's filter to the same month
        self.f_year_cb.set(date[:4])
        self.f_month_cb.set(date[5:7])
        self._load_history()

    def _safe_get(self, row, key, default=0):
        """Safely get a value from a sqlite3.Row even if key doesn't exist."""
        try:
            return row[key]
        except (IndexError, KeyError):
            return default

    # ─────────────────────── SAVE ────────────────────────────────────────────
    def _save_record(self):
        date = self.date_ent.get().strip()
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format.")
            return

        counts = self._get_denom_counts()
        upi    = self._get_upi()

        cash_total     = sum(d * counts[d] for d in DENOMS)
        total_received = cash_total + upi

        # Sum of employee expenses for this date (deduction)
        conn = self.db.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS tot FROM expenses WHERE date=?",
            (date,))
        daily_exp = cur.fetchone()["tot"]
        daily_net = total_received - daily_exp

        # Upsert: check if exists first
        cur.execute("SELECT date FROM cash_records WHERE date=?", (date,))
        exists = cur.fetchone()

        if exists:
            cur.execute(
                '''UPDATE cash_records SET
                     c2=?, c5=?, c10=?, c20=?, c50=?, c100=?, c200=?, c500=?,
                     upi_amount=?, cash_total=?, total_received=?,
                     daily_exp=?, daily_net=?
                   WHERE date=?''',
                (counts[2], counts[5], counts[10], counts[20],
                 counts[50], counts[100], counts[200], counts[500],
                 upi, cash_total, total_received,
                 daily_exp, daily_net, date)
            )
        else:
            cur.execute(
                '''INSERT INTO cash_records
                   (date, c2, c5, c10, c20, c50, c100, c200, c500,
                    upi_amount, cash_total, total_received, daily_exp, daily_net)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (date,
                 counts[2], counts[5], counts[10], counts[20],
                 counts[50], counts[100], counts[200], counts[500],
                 upi, cash_total, total_received, daily_exp, daily_net)
            )

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Saved ✔",
            f"Record for {date} saved!\n\n"
            f"Cash:    ₹{cash_total:,.2f}\n"
            f"UPI:     ₹{upi:,.2f}\n"
            f"Gross:   ₹{total_received:,.2f}\n"
            f"Expenses:₹{daily_exp:,.2f}\n"
            f"Net:     ₹{daily_net:,.2f}"
        )
        # Refresh history to same month as saved date
        self.f_year_cb.set(date[:4])
        self.f_month_cb.set(date[5:7])
        self._load_history()

    # ─────────────────────── LOAD HISTORY ────────────────────────────────────
    def _load_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        year  = self.f_year_cb.get()
        month = self.f_month_cb.get()
        patt  = f"{year}-{month}%"

        conn = self.db.get_connection()
        cur  = conn.cursor()
        cur.execute(
            '''SELECT date, c2, c5, c10, c20, c50, c100, c200, c500,
                      cash_total, upi_amount, total_received, daily_exp, daily_net
               FROM cash_records WHERE date LIKE ? ORDER BY date DESC''',
            (patt,))
        rows = cur.fetchall()
        conn.close()

        mon_gross = 0.0
        mon_net   = 0.0

        for r in rows:
            # Safely read daily_exp (might be 0 if column was just migrated)
            d_exp = self._safe_get(r, "daily_exp", 0)
            d_net = self._safe_get(r, "daily_net", 0)
            mon_gross += self._safe_get(r, "total_received", 0)
            mon_net   += d_net

            self.tree.insert("", "end", values=(
                r["date"],
                int(self._safe_get(r, "c2",   0)),
                int(self._safe_get(r, "c5",   0)),
                int(self._safe_get(r, "c10",  0)),
                int(self._safe_get(r, "c20",  0)),
                int(self._safe_get(r, "c50",  0)),
                int(self._safe_get(r, "c100", 0)),
                int(self._safe_get(r, "c200", 0)),
                int(self._safe_get(r, "c500", 0)),
                f"₹{self._safe_get(r,'cash_total',0):,.0f}",
                f"₹{self._safe_get(r,'upi_amount',0):,.0f}",
                f"₹{self._safe_get(r,'total_received',0):,.0f}",
                f"₹{d_exp:,.0f}",
                f"₹{d_net:,.0f}",
            ))

        self.month_total_lbl.config(
            text=f"Month Gross: ₹{mon_gross:,.2f}  |  Month Net: ₹{mon_net:,.2f}"
        )

    # ─────────────────────── ROW SELECT → LOAD FORM ───────────────────────────
    def _on_row_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        date_val = str(self.tree.item(sel[0])["values"][0])
        self.date_ent.delete(0, "end")
        self.date_ent.insert(0, date_val)
        self._load_by_date()
