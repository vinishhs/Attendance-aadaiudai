import sqlite3
import os
import shutil
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="dress_shop.db"):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # 1. Employees
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                emp_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                gender      TEXT,
                phone       TEXT,
                address     TEXT,
                designation TEXT,
                base_salary REAL NOT NULL DEFAULT 0,
                joining_date TEXT,
                photo_path  TEXT
            )
        ''')

        # 2. Attendance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id           INTEGER NOT NULL,
                date             TEXT NOT NULL,
                status           TEXT NOT NULL DEFAULT 'A',
                permission_hours REAL DEFAULT 0,
                FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
            )
        ''')
        # Add UNIQUE index if not exists (handles old DB without UNIQUE constraint)
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_att_emp_date
            ON attendance(emp_id, date)
        ''')

        # 3. Expenses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id     INTEGER NOT NULL,
                date       TEXT NOT NULL,
                reason     TEXT,
                amount     REAL NOT NULL DEFAULT 0,
                month_year TEXT NOT NULL,
                FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
            )
        ''')

        # 4. Payroll
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payroll (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id         INTEGER NOT NULL,
                month_year     TEXT NOT NULL,
                payable_days   REAL DEFAULT 0,
                base_salary    REAL DEFAULT 0,
                one_day_salary REAL DEFAULT 0,
                total_expenses REAL DEFAULT 0,
                net_salary     REAL DEFAULT 0,
                calculated_at  TEXT,
                FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_payroll_emp_month
            ON payroll(emp_id, month_year)
        ''')

        # 5. Daily Cash Records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cash_records (
                date           TEXT PRIMARY KEY,
                c2             INTEGER DEFAULT 0,
                c5             INTEGER DEFAULT 0,
                c10            INTEGER DEFAULT 0,
                c20            INTEGER DEFAULT 0,
                c50            INTEGER DEFAULT 0,
                c100           INTEGER DEFAULT 0,
                c200           INTEGER DEFAULT 0,
                c500           INTEGER DEFAULT 0,
                upi_amount     REAL DEFAULT 0,
                cash_total     REAL DEFAULT 0,
                total_received REAL DEFAULT 0,
                daily_net      REAL DEFAULT 0
            )
        ''')

        # 6. Backup Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT,
                backup_path TEXT,
                status      TEXT
            )
        ''')

        conn.commit()

        # ── MIGRATIONS: add columns to old databases ──────────────────────────
        self._migrate(cursor, conn)

        conn.commit()
        conn.close()

    def _migrate(self, cursor, conn):
        """Safely add new columns to existing tables if they don't exist yet."""
        def add_col(table, col, typedef):
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}")
                conn.commit()
            except Exception:
                pass  # column already exists

        # cash_records: old DB had no daily_exp column
        add_col("cash_records", "daily_exp", "REAL DEFAULT 0")

        # employees: ensure all columns exist
        add_col("employees", "designation", "TEXT")
        add_col("employees", "address",     "TEXT")

    # ── Payroll computation ───────────────────────────────────────────────────
    def compute_payroll(self, emp_id, month_year):
        """(Re)compute & upsert payroll for one employee for one month (MM-YYYY)."""
        parts = month_year.split("-")
        mm, yyyy = parts[0], parts[1]
        date_pattern = f"{yyyy}-{mm}%"

        conn = self.get_connection()
        cur  = conn.cursor()

        cur.execute("SELECT base_salary FROM employees WHERE emp_id=?", (emp_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return
        base_salary = row["base_salary"]

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM attendance "
            "WHERE emp_id=? AND date LIKE ? AND status IN ('P','PL','PP')",
            (emp_id, date_pattern)
        )
        payable_days = cur.fetchone()["cnt"]

        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS tot FROM expenses "
            "WHERE emp_id=? AND month_year=?",
            (emp_id, month_year)
        )
        total_expenses = cur.fetchone()["tot"]

        one_day_salary = base_salary / 30.0
        net_salary     = (payable_days * one_day_salary) - total_expenses
        now_str        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Use INSERT OR REPLACE via the unique index
        cur.execute(
            "SELECT id FROM payroll WHERE emp_id=? AND month_year=?",
            (emp_id, month_year)
        )
        existing = cur.fetchone()

        if existing:
            cur.execute(
                '''UPDATE payroll SET payable_days=?, base_salary=?, one_day_salary=?,
                                     total_expenses=?, net_salary=?, calculated_at=?
                   WHERE id=?''',
                (payable_days, base_salary, one_day_salary,
                 total_expenses, net_salary, now_str, existing["id"])
            )
        else:
            cur.execute(
                '''INSERT INTO payroll
                   (emp_id, month_year, payable_days, base_salary, one_day_salary,
                    total_expenses, net_salary, calculated_at)
                   VALUES (?,?,?,?,?,?,?,?)''',
                (emp_id, month_year, payable_days, base_salary,
                 one_day_salary, total_expenses, net_salary, now_str)
            )
        conn.commit()
        conn.close()

    # ── Backup ────────────────────────────────────────────────────────────────
    def backup_database(self):
        try:
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(backup_dir, f"dress_shop_backup_{ts}.db")
            shutil.copy2(self.db_path, dest)

            conn = self.get_connection()
            conn.execute(
                "INSERT INTO backup_logs (timestamp, backup_path, status) VALUES (?,?,?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), dest, "Success")
            )
            conn.commit()
            conn.close()
            return True, dest
        except Exception as e:
            return False, str(e)


if __name__ == "__main__":
    db = DatabaseManager()
    print("Database ready:", db.db_path)
