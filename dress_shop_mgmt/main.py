import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os, sys

# ── Ensure script CWD points to this file so assets/db are found correctly ──
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from views.employee_view  import EmployeeView
from views.attendance_view import AttendanceView
from views.expense_view   import ExpenseView
from views.payroll_view   import PayrollView
from views.money_view     import MoneyView

# ─────────────────────────── CONSTANTS ──────────────────────────────────────
ADMIN_EMAIL    = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"
SHOP_NAME      = "AADAI UDAI"

THEME = {
    "primary":     "#F43F5E",
    "primary_dk":  "#BE123C",
    "secondary":   "#6366F1",
    "bg_dark":     "#0F172A",
    "bg_sidebar":  "#1E293B",
    "bg_page":     "#F1F5F9",
    "bg_card":     "#FFFFFF",
    "text_main":   "#0F172A",
    "text_muted":  "#64748B",
    "text_on_dark":"#F8FAFC",
    "success":     "#10B981",
    "border":      "#E2E8F0",
}

NAV_ITEMS = {
    "employees": ("👥", "Staff Directory"),
    "attendance": ("📅", "Daily Attendance"),
    "expenses":  ("💸", "Store Expenses"),
    "payroll":   ("💰", "Payroll Engine"),
    "money":     ("🏧", "Vault & Cash"),
}

TITLE_MAP = {
    "employees": "Human Resources Management",
    "attendance": "Staff Attendance Logs",
    "expenses":  "Operational Expenditure",
    "payroll":   "Payroll Registry & Dispensation",
    "money":     "Boutique Cash Flow & Vault",
}

# ──────────────────────────── NAV BUTTON ─────────────────────────────────────
class NavButton(tk.Button):
    def __init__(self, master, text, command, active=False, **kw):
        self._active = active
        bg = THEME["primary"] if active else THEME["bg_sidebar"]
        super().__init__(master, text=text, command=command,
                         bg=bg, fg="white",
                         font=("Segoe UI Variable Text", 10, "bold" if active else "normal"),
                         bd=0, activebackground=THEME["primary"],
                         activeforeground="white",
                         cursor="hand2", padx=22, pady=13, anchor="w", **kw)
        self.bind("<Enter>", self._hover_in)
        self.bind("<Leave>", self._hover_out)

    def _hover_in(self, _):
        if not self._active:
            self.config(bg="#334155")

    def _hover_out(self, _):
        if not self._active:
            self.config(bg=THEME["bg_sidebar"])

# ──────────────────────────── MAIN APP ───────────────────────────────────────
class DressShopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{SHOP_NAME}  |  Boutique ERP Suite")
        self.root.state("zoomed")
        self.root.configure(bg=THEME["bg_page"])
        self.db = DatabaseManager()
        self._apply_styles()
        self._show_login()

    # ── Styles ────────────────────────────────────────────────────────────────
    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=THEME["bg_card"],
                        foreground=THEME["text_main"],
                        rowheight=38,
                        fieldbackground=THEME["bg_card"],
                        font=("Segoe UI", 10),
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        font=("Segoe UI Semibold", 9),
                        background="#F8FAFC",
                        foreground=THEME["text_muted"],
                        relief="flat", padding=8)
        style.map("Treeview", background=[("selected", THEME["primary"])])
        style.configure("Vertical.TScrollbar",
                        gripcount=0,
                        background=THEME["border"],
                        troughcolor=THEME["bg_page"])
        style.configure("Horizontal.TScrollbar",
                        gripcount=0,
                        background=THEME["border"],
                        troughcolor=THEME["bg_page"])
        style.configure("TCombobox",
                        selectbackground=THEME["primary"],
                        fieldbackground="#F8FAFC",
                        background="#F8FAFC")

    # ── LOGIN SCREEN ──────────────────────────────────────────────────────────
    def _show_login(self):
        self._clear_screen()

        bg = tk.Frame(self.root, bg=THEME["bg_dark"])
        bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        card = tk.Frame(bg, bg=THEME["bg_card"])
        card.place(relx=0.5, rely=0.5, anchor="center", width=880, height=520)

        # Left accent
        left = tk.Frame(card, bg=THEME["primary"], width=360)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Label(left, text="✧",
                 font=("Segoe UI", 80), bg=THEME["primary"], fg="white").place(relx=0.5, rely=0.3, anchor="center")
        tk.Label(left, text=SHOP_NAME,
                 font=("Segoe UI Variable Display", 30, "bold"),
                 bg=THEME["primary"], fg="white").place(relx=0.5, rely=0.48, anchor="center")
        tk.Label(left, text="BOUTIQUE  ERP  SUITE",
                 font=("Segoe UI Semibold", 9),
                 bg=THEME["primary"], fg="#FECDD3").place(relx=0.5, rely=0.56, anchor="center")
        tk.Label(left, text="© 2025 Aadai Udai",
                 font=("Segoe UI", 7),
                 bg=THEME["primary"], fg="#FECDD3").place(relx=0.5, rely=0.92, anchor="center")

        # Right form
        right = tk.Frame(card, bg=THEME["bg_card"], padx=60)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(right, text="Administrator Login",
                 font=("Segoe UI Variable Display", 22, "bold"),
                 bg=THEME["bg_card"], fg=THEME["text_main"]).pack(pady=(60,6), anchor="w")
        tk.Label(right, text="Enter your credentials to access the system.",
                 font=("Segoe UI", 10),
                 bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(pady=(0,36), anchor="w")

        def make_entry(lbl, *, show="", default=""):
            tk.Label(right, text=lbl, font=("Segoe UI Semibold", 8),
                     bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(anchor="w")
            f = tk.Frame(right, bg="#F8FAFC", pady=1)
            f.pack(fill="x", pady=(4,4))
            e = tk.Entry(f, font=("Segoe UI", 12), bd=0, bg="#F8FAFC", show=show)
            e.pack(fill="x", padx=10, ipady=8)
            if default:
                e.insert(0, default)
            tk.Frame(right, bg=THEME["border"], height=1).pack(fill="x", pady=(0,14))
            return e

        self._email_ent = make_entry("EMAIL ADDRESS")
        self._pass_ent  = make_entry("PASSWORD", show="●")

        # Error label
        self._login_err = tk.Label(right, text="",
                                    font=("Segoe UI Semibold", 9),
                                    bg=THEME["bg_card"], fg="#EF4444")
        self._login_err.pack(anchor="w", pady=(0,6))

        btn = tk.Button(right, text="🔓  SIGN IN",
                        command=self._handle_login,
                        bg=THEME["bg_dark"], fg="white",
                        font=("Segoe UI Variable Text", 11, "bold"),
                        bd=0, cursor="hand2", pady=14,
                        activebackground=THEME["primary"])
        btn.pack(fill="x")
        # Bind Enter key
        self.root.bind("<Return>", lambda e: self._handle_login())

        tk.Label(right, text="Offline Mode • Data is stored locally",
                 font=("Segoe UI", 8),
                 bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(side="bottom", pady=18)

    def _handle_login(self):
        email = self._email_ent.get().strip()
        pwd   = self._pass_ent.get()
        if email == ADMIN_EMAIL and pwd == ADMIN_PASSWORD:
            self.root.unbind("<Return>")
            self._show_dashboard()
        else:
            self._login_err.config(text="⚠  Incorrect email or password. Please try again.")

    # ── DASHBOARD ─────────────────────────────────────────────────────────────
    def _show_dashboard(self):
        self._clear_screen()

        # ─ Sidebar ─
        sidebar = tk.Frame(self.root, bg=THEME["bg_sidebar"], width=270)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo header
        hdr = tk.Frame(sidebar, bg=THEME["bg_dark"], pady=28)
        hdr.pack(fill="x")
        tk.Label(hdr, text="AU",
                 font=("Segoe UI Variable Display", 30, "bold"),
                 bg=THEME["bg_dark"], fg=THEME["primary"]).pack()
        tk.Label(hdr, text=SHOP_NAME,
                 font=("Segoe UI Semibold", 9),
                 bg=THEME["bg_dark"], fg="white").pack()

        # Clock label
        self._clock_lbl = tk.Label(sidebar, text="",
                                    font=("Segoe UI", 8),
                                    bg=THEME["bg_sidebar"], fg=THEME["text_muted"])
        self._clock_lbl.pack(pady=(8,0))
        self._update_clock()

        # Nav buttons
        nav_frame = tk.Frame(sidebar, bg=THEME["bg_sidebar"], pady=14)
        nav_frame.pack(fill="both", expand=True)

        self._nav_btns: dict[str, NavButton] = {}
        for key, (icon, label) in NAV_ITEMS.items():
            btn = NavButton(nav_frame,
                            text=f"  {icon}   {label}",
                            command=lambda k=key: self._switch_tab(k),
                            active=(key == "employees"))
            btn.pack(fill="x")
            self._nav_btns[key] = btn

        # Footer buttons
        footer = tk.Frame(sidebar, bg=THEME["bg_sidebar"], pady=14)
        footer.pack(side="bottom", fill="x")
        NavButton(footer, text="  💾   Backup Data", command=self._do_backup).pack(fill="x")
        NavButton(footer, text="  🚪   Sign Out",    command=self._handle_logout).pack(fill="x")

        # ─ Main area ─
        main_area = tk.Frame(self.root, bg=THEME["bg_page"])
        main_area.pack(side="right", fill="both", expand=True)

        # Top bar
        topbar = tk.Frame(main_area, bg=THEME["bg_card"], height=72, padx=36)
        topbar.pack(side="top", fill="x")
        topbar.pack_propagate(False)
        topbar.config(highlightbackground=THEME["border"], highlightthickness=1)

        self._view_title = tk.Label(topbar,
                                     text="Human Resources Management",
                                     font=("Segoe UI Variable Display", 18, "bold"),
                                     bg=THEME["bg_card"], fg=THEME["text_main"])
        self._view_title.pack(side="left", fill="y")

        # Admin badge
        badge = tk.Frame(topbar, bg="#F8FAFC", padx=14, pady=6)
        badge.pack(side="right", pady=14)
        tk.Label(badge, text=" A ",
                 font=("Segoe UI", 9, "bold"),
                 bg=THEME["secondary"], fg="white").pack(side="left", padx=(0,8))
        tk.Label(badge, text="System Admin",
                 font=("Segoe UI Semibold", 9),
                 bg="#F8FAFC", fg=THEME["text_main"]).pack(side="left")

        # Content container
        self._content = tk.Frame(main_area, bg=THEME["bg_page"], padx=36, pady=30)
        self._content.pack(fill="both", expand=True)

        self._current_view = None
        self._switch_tab("employees")

    def _update_clock(self):
        now = datetime.now().strftime("%d %b %Y  •  %I:%M %p")
        self._clock_lbl.config(text=now)
        self.root.after(30000, self._update_clock)

    def _switch_tab(self, key: str):
        if self._current_view:
            self._current_view.destroy()

        for k, btn in self._nav_btns.items():
            is_act = (k == key)
            btn._active = is_act
            btn.config(
                bg=THEME["primary"] if is_act else THEME["bg_sidebar"],
                font=("Segoe UI Variable Text", 10, "bold" if is_act else "normal")
            )

        self._view_title.config(text=TITLE_MAP.get(key, "Dashboard"))

        view_classes = {
            "employees": EmployeeView,
            "attendance": AttendanceView,
            "expenses":  ExpenseView,
            "payroll":   PayrollView,
            "money":     MoneyView,
        }
        cls = view_classes.get(key)
        if cls:
            self._current_view = cls(self._content, self.db)
            self._current_view.pack(fill="both", expand=True)

    # ── Backup ────────────────────────────────────────────────────────────────
    def _do_backup(self):
        ok, result = self.db.backup_database()
        if ok:
            messagebox.showinfo("Backup Successful",
                                f"✔ Database backed up to:\n{result}")
        else:
            messagebox.showerror("Backup Failed", f"Error: {result}")

    # ── Logout ────────────────────────────────────────────────────────────────
    def _handle_logout(self):
        if messagebox.askyesno("Sign Out",
                               "Save a backup and sign out?"):
            self._do_backup()
            self._show_login()

    def _clear_screen(self):
        for w in self.root.winfo_children():
            w.destroy()


# ──────────────────────────── ENTRY POINT ────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.minsize(1100, 650)
    app = DressShopApp(root)
    root.mainloop()
