"""
Student Expense Tracker (Professional - GitHub-ready)
File: src/tracker.py

Features included:
- OOP: ExpenseTracker class
- Tkinter GUI with Treeview for listing entries
- Add / Edit / Delete entries
- CSV storage (data/expenses.csv) with unique ID
- Monthly summary, filter by date range
- Budget system with alerts
- Category pie chart (matplotlib)
- Export to CSV & Excel (openpyxl optional)
- Simple logging & docstrings

Run:
    python src/tracker.py

Dependencies (requirements.txt):
    matplotlib
    openpyxl  # optional, only for Excel export

"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
from datetime import datetime
import uuid
import logging

# Optional import for Excel export
try:
    import openpyxl
    EXCEL_AVAILABLE = True
except Exception:
    EXCEL_AVAILABLE = False

# Matplotlib for charts
import matplotlib.pyplot as plt

# ---------- Configuration ----------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
FILE_NAME = os.path.join(DATA_DIR, "expenses.csv")
LOG_FILE = os.path.join(DATA_DIR, "tracker.log")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Setup basic logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

# CSV header
CSV_FIELDS = ["ID", "Date", "Type", "Amount", "Category", "Note"]


# ---------- Utility Functions ----------
def ensure_file():
    """Create CSV file with header if it doesn't exist."""
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, mode="w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_FIELDS)
        logging.info("Created new data file: %s", FILE_NAME)


def read_entries():
    """Read all entries from CSV and return a list of dicts."""
    ensure_file()
    entries = []
    with open(FILE_NAME, mode="r", newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # normalize types
            row['Amount'] = float(row['Amount'])
            entries.append(row)
    return entries


def write_entries(entries):
    """Overwrite CSV with the provided list of entry dicts."""
    ensure_file()
    with open(FILE_NAME, mode="w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for e in entries:
            writer.writerow({k: e[k] for k in CSV_FIELDS})
    logging.info("Wrote %d entries to file", len(entries))


def append_entry(entry):
    """Append a single entry dict to CSV."""
    ensure_file()
    with open(FILE_NAME, mode="a", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow({k: entry[k] for k in CSV_FIELDS})
    logging.info("Appended entry ID=%s", entry['ID'])


# ---------- Main Application Class ----------
class ExpenseTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Expense Tracker")
        self.geometry("880x600")
        self.resizable(True, True)

        # State
        self.entries = []
        self.budget = None  # budget as float or None

        # Build UI
        self._build_ui()
        self._load_entries()

    # ---------------- UI BUILD ----------------
    def _build_ui(self):
        # Top frame: input
        top = ttk.Frame(self, padding=8)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Category:").grid(row=0, column=0, sticky=tk.W)
        self.category_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.category_var, width=20).grid(row=0, column=1, padx=4)

        ttk.Label(top, text="Amount (₹):").grid(row=0, column=2, sticky=tk.W)
        self.amount_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.amount_var, width=12).grid(row=0, column=3, padx=4)

        ttk.Label(top, text="Type:").grid(row=0, column=4, sticky=tk.W)
        self.type_var = tk.StringVar(value="Expense")
        ttk.Combobox(top, textvariable=self.type_var, values=["Expense", "Income"], width=10, state="readonly").grid(row=0, column=5, padx=4)

        ttk.Label(top, text="Note:").grid(row=1, column=0, sticky=tk.W)
        self.note_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.note_var, width=40).grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=4, pady=6)

        add_btn = ttk.Button(top, text="➕ Add", command=self.add_entry)
        add_btn.grid(row=0, column=6, rowspan=2, padx=6)

        # Budget controls
        budget_frame = ttk.Frame(top)
        budget_frame.grid(row=0, column=7, rowspan=2, padx=8)
        ttk.Label(budget_frame, text="Monthly Budget (₹):").grid(row=0, column=0)
        self.budget_var = tk.StringVar()
        ttk.Entry(budget_frame, textvariable=self.budget_var, width=12).grid(row=1, column=0)
        ttk.Button(budget_frame, text="Set Budget", command=self.set_budget).grid(row=2, column=0, pady=4)

        # Middle frame: treeview
        mid = ttk.Frame(self, padding=8)
        mid.pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Date", "Type", "Amount", "Category", "Note")
        self.tree = ttk.Treeview(mid, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            # set decent width
            if col == 'Note':
                self.tree.column(col, width=220)
            elif col == 'Category':
                self.tree.column(col, width=120)
            elif col == 'Amount':
                self.tree.column(col, width=80, anchor=tk.E)
            else:
                self.tree.column(col, width=120)

        vsb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(mid, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        mid.grid_rowconfigure(0, weight=1)
        mid.grid_columnconfigure(0, weight=1)

        # Right-click menu for edit/delete
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Edit", command=self._on_edit_selected)
        self.menu.add_command(label="Delete", command=self._on_delete_selected)
        self.tree.bind("<Button-3>", self._show_context_menu)

        # Bottom frame: actions
        bottom = ttk.Frame(self, padding=8)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(bottom, text="📊 Show Category Chart", command=self.show_chart).pack(side=tk.LEFT, padx=6)
        ttk.Button(bottom, text="📑 Show Summary", command=self.show_summary).pack(side=tk.LEFT, padx=6)

        ttk.Button(bottom, text="🔍 Filter by Month", command=self._open_month_filter).pack(side=tk.LEFT, padx=6)
        ttk.Button(bottom, text="📥 Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=6)
        ttk.Button(bottom, text="📥 Export Excel", command=self.export_excel).pack(side=tk.LEFT, padx=6)

        ttk.Button(bottom, text="Refresh", command=self._load_entries).pack(side=tk.RIGHT, padx=6)

    # ---------------- Data operations ----------------
    def _load_entries(self):
        """Load entries from file into memory and populate Treeview."""
        self.entries = read_entries()
        self._populate_tree()

    def _populate_tree(self, entries=None):
        """Populate the Treeview widget with entries."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        use = entries if entries is not None else self.entries
        for e in use:
            self.tree.insert('', tk.END, values=(e['ID'], e['Date'], e['Type'], f"{float(e['Amount']):.2f}", e['Category'], e['Note']))

    def add_entry(self):
        """Collect input fields, validate and append entry."""
        cat = self.category_var.get().strip()
        amt = self.amount_var.get().strip()
        typ = self.type_var.get()
        note = self.note_var.get().strip()

        if not cat or not amt:
            messagebox.showerror("Validation Error", "Category and Amount are required.")
            return
        try:
            amt_f = float(amt)
        except ValueError:
            messagebox.showerror("Validation Error", "Amount must be a number.")
            return

        entry = {
            'ID': str(uuid.uuid4()),
            'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Type': typ,
            'Amount': f"{amt_f:.2f}",
            'Category': cat,
            'Note': note,
        }
        append_entry(entry)
        self.entries.append(entry)
        self._populate_tree()
        logging.info("Added entry: %s", entry['ID'])

        # clear inputs
        self.category_var.set("")
        self.amount_var.set("")
        self.note_var.set("")

        # budget check
        if self.budget is not None and typ == 'Expense':
            total_exp = sum(float(e['Amount']) for e in self.entries if e['Type'] == 'Expense')
            if total_exp > self.budget:
                messagebox.showwarning("Budget Exceeded", f"You have exceeded your budget of ₹{self.budget:.2f}\.\nTotal expense: ₹{total_exp:.2f}")

    def _on_edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        entry_id = item['values'][0]
        self._open_edit_window(entry_id)

    def _on_delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        entry_id = item['values'][0]
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this entry?"):
            self.entries = [e for e in self.entries if e['ID'] != entry_id]
            write_entries(self.entries)
            self._populate_tree()

    def _show_context_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _open_edit_window(self, entry_id):
        entry = next((e for e in self.entries if e['ID'] == entry_id), None)
        if not entry:
            messagebox.showerror("Error", "Entry not found")
            return

        win = tk.Toplevel(self)
        win.title("Edit Entry")

        ttk.Label(win, text="Category:").grid(row=0, column=0, sticky=tk.W, padx=6, pady=6)
        cat_v = tk.StringVar(value=entry['Category'])
        ttk.Entry(win, textvariable=cat_v).grid(row=0, column=1, padx=6)

        ttk.Label(win, text="Amount:").grid(row=1, column=0, sticky=tk.W, padx=6, pady=6)
        amt_v = tk.StringVar(value=entry['Amount'])
        ttk.Entry(win, textvariable=amt_v).grid(row=1, column=1, padx=6)

        ttk.Label(win, text="Type:").grid(row=2, column=0, sticky=tk.W, padx=6, pady=6)
        type_v = tk.StringVar(value=entry['Type'])
        ttk.Combobox(win, textvariable=type_v, values=["Expense", "Income"], state='readonly').grid(row=2, column=1, padx=6)

        ttk.Label(win, text="Note:").grid(row=3, column=0, sticky=tk.W, padx=6, pady=6)
        note_v = tk.StringVar(value=entry['Note'])
        ttk.Entry(win, textvariable=note_v, width=40).grid(row=3, column=1, padx=6)

        def save_changes():
            try:
                new_amt = float(amt_v.get())
            except ValueError:
                messagebox.showerror("Validation Error", "Amount must be a number.")
                return
            entry['Category'] = cat_v.get().strip()
            entry['Amount'] = f"{new_amt:.2f}"
            entry['Type'] = type_v.get()
            entry['Note'] = note_v.get().strip()
            write_entries(self.entries)
            self._populate_tree()
            win.destroy()

        ttk.Button(win, text="Save", command=save_changes).grid(row=4, column=0, columnspan=2, pady=8)

    # ---------------- Summaries & Charts ----------------
    def show_summary(self, entries=None):
        """Compute total income/expense and show messagebox."""
        use = entries if entries is not None else self.entries
        income = sum(float(e['Amount']) for e in use if e['Type'] == 'Income')
        expense = sum(float(e['Amount']) for e in use if e['Type'] == 'Expense')
        balance = income - expense
        msg = f"💰 Total Income: ₹{income:.2f}\n💸 Total Expense: ₹{expense:.2f}\n📌 Balance: ₹{balance:.2f}"
        if self.budget is not None:
            msg += f"\n\nMonthly Budget: ₹{self.budget:.2f}"
        messagebox.showinfo("Summary", msg)

    def show_chart(self, entries=None):
        """Show pie chart of category-wise expenses."""
        use = entries if entries is not None else self.entries
        categories = {}
        for e in use:
            if e['Type'] == 'Expense':
                categories[e['Category']] = categories.get(e['Category'], 0) + float(e['Amount'])
        if not categories:
            messagebox.showinfo("Info", "No expenses to show in chart")
            return
        plt.figure(figsize=(6, 6))
        plt.pie(list(categories.values()), labels=list(categories.keys()), autopct="%1.1f%%")
        plt.title("Expense Breakdown by Category")
        plt.tight_layout()
        plt.show()

    # ---------------- Filters ----------------
    def _open_month_filter(self):
        win = tk.Toplevel(self)
        win.title("Filter by Month")

        ttk.Label(win, text="Enter month (YYYY-MM):").grid(row=0, column=0, padx=6, pady=6)
        month_v = tk.StringVar()
        ttk.Entry(win, textvariable=month_v).grid(row=0, column=1, padx=6)

        def apply_filter():
            m = month_v.get().strip()
            if not m:
                messagebox.showerror("Input Error", "Please enter month in format YYYY-MM")
                return
            filtered = [e for e in self.entries if e['Date'].startswith(m)]
            if not filtered:
                messagebox.showinfo("No Data", f"No records for {m}")
            self._populate_tree(filtered)
            win.destroy()

        ttk.Button(win, text="Apply", command=apply_filter).grid(row=1, column=0, columnspan=2, pady=8)

    # ---------------- Budget ----------------
    def set_budget(self):
        b = self.budget_var.get().strip()
        if not b:
            self.budget = None
            messagebox.showinfo("Budget", "Budget cleared")
            return
        try:
            bf = float(b)
        except ValueError:
            messagebox.showerror("Validation Error", "Budget must be a number.")
            return
        self.budget = bf
        messagebox.showinfo("Budget Set", f"Monthly budget set to ₹{self.budget:.2f}")

    # ---------------- Export ----------------
    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[("CSV files", '*.csv')])
        if not path:
            return
        write_entries(self.entries)
        # simply copy the data file to chosen path
        with open(FILE_NAME, 'r', encoding='utf-8') as src, open(path, 'w', encoding='utf-8', newline='') as dst:
            dst.write(src.read())
        messagebox.showinfo("Export", f"Exported CSV to {path}")

    def export_excel(self):
        if not EXCEL_AVAILABLE:
            messagebox.showerror("Dependency Missing", "openpyxl not installed. Install it to export Excel files.")
            return
        path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[("Excel files", '*.xlsx')])
        if not path:
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Expenses"
        ws.append(CSV_FIELDS)
        for e in self.entries:
            ws.append([e[f] for f in CSV_FIELDS])
        wb.save(path)
        messagebox.showinfo("Export", f"Exported Excel to {path}")


# ---------- CLI Launch ----------
if __name__ == '__main__':
    ensure_file()
    app = ExpenseTracker()
    app.mainloop()
