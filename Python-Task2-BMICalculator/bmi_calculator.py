
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
import math
from pathlib import Path
from datetime import datetime

# =====================================================
# CONFIGURATION
# =====================================================

DB_PATH = Path(__file__).resolve().parent / "bmi_records.db"

BG = "#F4F1FF"
CARD = "#FFFFFF"
PURPLE = "#7354E8"
PURPLE_DARK = "#5C3FD1"
TEXT = "#292642"
MUTED = "#89869F"
BORDER = "#E8E3F6"

CATEGORY_COLORS = {
    "Underweight": "#4285D4",
    "Normal": "#24A879",
    "Overweight": "#E9A23B",
    "Obese": "#E65B70",
}


# =====================================================
# DATABASE
# =====================================================

def create_database():
    """Create the database table if it does not exist."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bmi_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                weight REAL NOT NULL,
                height REAL NOT NULL,
                bmi REAL NOT NULL,
                category TEXT NOT NULL,
                recorded_at TEXT NOT NULL
            )
        """)


def get_records(user_name=None):
    """Get saved records, newest first."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row

        if user_name:
            rows = conn.execute("""
                SELECT id, user_name, weight, height,
                       bmi, category, recorded_at
                FROM bmi_records
                WHERE user_name = ?
                ORDER BY id DESC
            """, (user_name,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, user_name, weight, height,
                       bmi, category, recorded_at
                FROM bmi_records
                ORDER BY id DESC
            """).fetchall()

    return [dict(row) for row in rows]


# =====================================================
# BMI LOGIC
# =====================================================

def calculate_bmi(weight, height):
    if not math.isfinite(weight) or not math.isfinite(height):
        raise ValueError("Enter valid numbers.")

    if weight <= 0 or height <= 0:
        raise ValueError("Weight and height must be positive.")

    return round(weight / (height ** 2), 2)


def classify_bmi(bmi):
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


# =====================================================
# SUMMARY CARDS AND HISTORY
# =====================================================

def refresh_dashboard():
    """Update all summary values and history records."""
    try:
        records = get_records()
    except sqlite3.Error as error:
        messagebox.showerror("Database Error", str(error))
        return

    count = len(records)

    # Update summary labels directly.
    total_value.config(text=str(count))

    if count == 0:
        average_value.config(text="--")
        latest_value.config(text="--")
        latest_category.config(
            text="No records yet",
            fg=MUTED
        )
    else:
        average = sum(
            float(record["bmi"]) for record in records
        ) / count

        latest = records[0]

        average_value.config(text=f"{average:.2f}")
        latest_value.config(text=f'{latest["bmi"]:.2f}')

        latest_category.config(
            text=latest["category"],
            fg=CATEGORY_COLORS.get(latest["category"], TEXT)
        )

    # Clear old history.
    for item in history_tree.get_children():
        history_tree.delete(item)

    # Insert updated records.
    for record in records:
        try:
            display_date = datetime.strptime(
                record["recorded_at"],
                "%Y-%m-%d %H:%M:%S"
            ).strftime("%d %b %Y, %I:%M %p")
        except (ValueError, TypeError):
            display_date = str(record["recorded_at"])

        history_tree.insert(
            "",
            tk.END,
            values=(
                record["user_name"],
                f'{record["bmi"]:.2f}',
                record["category"],
                f'{record["weight"]:.1f}',
                f'{record["height"] * 100:.1f}',
                display_date
            ),
            tags=(record["category"],)
        )

    for category, color in CATEGORY_COLORS.items():
        history_tree.tag_configure(
            category,
            foreground=color
        )

    # Refresh user dropdown.
    names = sorted({
        record["user_name"] for record in records
    })

    user_combo["values"] = names

    if selected_user.get() in names:
        user_combo.set(selected_user.get())
    elif names:
        selected_user.set(names[0])
        user_combo.set(names[0])
    else:
        selected_user.set("")
        user_combo.set("")


# =====================================================
# CALCULATE AND SAVE BMI
# =====================================================

def calculate_and_save():
    name = name_entry.get().strip()
    weight_text = weight_entry.get().strip()
    height_text = height_entry.get().strip()

    if not name:
        messagebox.showwarning(
            "Missing Name",
            "Please enter your name."
        )
        name_entry.focus_set()
        return

    if not weight_text or not height_text:
        messagebox.showwarning(
            "Missing Details",
            "Please enter weight and height."
        )
        return

    try:
        weight_input = float(weight_text)
        height_input = float(height_text)

        if not math.isfinite(weight_input):
            raise ValueError

        if not math.isfinite(height_input):
            raise ValueError

        if weight_input <= 0 or height_input <= 0:
            raise ValueError

        # Convert inputs to standard units for storage.
        if units.get() == "Metric (kg / cm)":
            weight_kg = weight_input
            height_m = height_input / 100
        else:
            weight_kg = weight_input * 0.45359237
            height_m = height_input * 0.0254

        if not 20 <= height_m * 100 <= 300:
            messagebox.showerror(
                "Invalid Height",
                "Height must be between 20 and 300 cm."
            )
            return

        if not 1 <= weight_kg <= 500:
            messagebox.showerror(
                "Invalid Weight",
                "Weight must be between 1 and 500 kg."
            )
            return

        bmi = calculate_bmi(weight_kg, height_m)
        category = classify_bmi(bmi)

    except (ValueError, OverflowError):
        messagebox.showerror(
            "Invalid Input",
            "Enter valid positive numbers for weight and height."
        )
        return

    recorded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                INSERT INTO bmi_records
                (user_name, weight, height, bmi, category, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name,
                weight_kg,
                height_m,
                bmi,
                category,
                recorded_at
            ))

    except sqlite3.Error as error:
        messagebox.showerror("Save Failed", str(error))
        return

    result_bmi.config(text=f"{bmi:.2f}")
    result_category.config(
        text=category,
        fg=CATEGORY_COLORS.get(category, TEXT)
    )

    selected_user.set(name)
    user_combo.set(name)

    refresh_dashboard()

    messagebox.showinfo(
        "BMI Saved",
        f"Record saved successfully!\n\n"
        f"Name: {name}\n"
        f"BMI: {bmi:.2f}\n"
        f"Category: {category}"
    )


# =====================================================
# INPUT CONTROLS
# =====================================================

def clear_fields():
    name_entry.delete(0, tk.END)
    weight_entry.delete(0, tk.END)
    height_entry.delete(0, tk.END)

    result_bmi.config(text="--")
    result_category.config(
        text="Waiting for calculation",
        fg=MUTED
    )

    name_entry.focus_set()


def update_unit_labels(_event=None):
    weight_entry.delete(0, tk.END)
    height_entry.delete(0, tk.END)

    if units.get() == "Metric (kg / cm)":
        weight_label.config(text="Weight (kg)")
        height_label.config(text="Height (cm)")
    else:
        weight_label.config(text="Weight (lbs)")
        height_label.config(text="Height (inches)")


# =====================================================
# CSV EXPORT
# =====================================================

def export_csv():
    destination = filedialog.asksaveasfilename(
        title="Export BMI History",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        initialfile="bmi_history.csv"
    )

    if not destination:
        return

    try:
        records = get_records()

        with open(
            destination,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:
            writer = csv.writer(file)
            writer.writerow([
                "ID", "Name", "Weight (kg)", "Height (m)",
                "BMI", "Category", "Recorded At"
            ])

            for record in records:
                writer.writerow([
                    record["id"],
                    record["user_name"],
                    record["weight"],
                    record["height"],
                    record["bmi"],
                    record["category"],
                    record["recorded_at"]
                ])

        messagebox.showinfo(
            "Export Complete",
            f"{len(records)} records exported successfully."
        )

    except (OSError, sqlite3.Error) as error:
        messagebox.showerror("Export Failed", str(error))


# =====================================================
# BMI TREND CHART
# =====================================================

def show_trend():
    name = user_combo.get().strip()

    if not name:
        messagebox.showwarning(
            "Select User",
            "Please select a user first."
        )
        return

    try:
        records = list(reversed(get_records(name)))
    except sqlite3.Error as error:
        messagebox.showerror("Database Error", str(error))
        return

    if not records:
        messagebox.showinfo(
            "No History",
            f"No records found for {name}."
        )
        return

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        messagebox.showerror(
            "Missing Library",
            "Install matplotlib with:\n"
            "python -m pip install matplotlib"
        )
        return

    dates = [record["recorded_at"] for record in records]
    values = [record["bmi"] for record in records]

    plt.figure(figsize=(9, 5))
    plt.plot(
        dates,
        values,
        marker="o",
        linewidth=2,
        color=PURPLE,
        label="BMI"
    )

    plt.axhline(
        18.5, linestyle="--",
        color="#4285D4", label="BMI 18.5"
    )
    plt.axhline(
        25, linestyle="--",
        color="#24A879", label="BMI 25"
    )
    plt.axhline(
        30, linestyle="--",
        color="#E65B70", label="BMI 30"
    )

    plt.title(f"BMI Progress - {name}")
    plt.xlabel("Date and Time")
    plt.ylabel("BMI")
    plt.xticks(rotation=35, ha="right")
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.show()


def on_history_double_click(_event=None):
    selection = history_tree.selection()

    if not selection:
        return

    values = history_tree.item(selection[0], "values")

    name_entry.delete(0, tk.END)
    name_entry.insert(0, values[0])

    selected_user.set(values[0])
    user_combo.set(values[0])


# =====================================================
# UI HELPERS
# =====================================================

def make_card(parent, title, subtitle=None):
    frame = tk.Frame(
        parent,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1,
        padx=16,
        pady=14
    )

    tk.Label(
        frame,
        text=title,
        font=("Segoe UI", 12, "bold"),
        bg=CARD,
        fg=TEXT
    ).pack(anchor="w")

    if subtitle:
        tk.Label(
            frame,
            text=subtitle,
            font=("Segoe UI", 9),
            bg=CARD,
            fg=MUTED,
            wraplength=400,
            justify="left"
        ).pack(anchor="w", pady=(4, 12))

    return frame


def make_button(parent, text, command, primary=False):
    background = PURPLE if primary else "#F0ECFF"
    foreground = "#FFFFFF" if primary else PURPLE_DARK

    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=background,
        fg=foreground,
        activebackground=PURPLE_DARK if primary else "#E4DCFF",
        activeforeground="#FFFFFF" if primary else PURPLE_DARK,
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        bd=0,
        padx=12,
        pady=9,
        cursor="hand2"
    )


# =====================================================
# MAIN APPLICATION
# =====================================================

create_database()

root = tk.Tk()
root.title("Health Tracker | BMI Dashboard")
root.geometry("1180x780")
root.minsize(1000, 680)
root.configure(bg=BG)

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background=CARD,
    fieldbackground=CARD,
    foreground=TEXT,
    rowheight=32,
    borderwidth=0,
    font=("Segoe UI", 9)
)

style.configure(
    "Treeview.Heading",
    background="#F0ECFF",
    foreground=TEXT,
    font=("Segoe UI", 9, "bold"),
    relief="flat",
    padding=8
)

style.map(
    "Treeview",
    background=[("selected", "#E7DFFF")],
    foreground=[("selected", TEXT)]
)

# ---------------- HEADER ----------------

header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=24, pady=(18, 12))

tk.Label(
    header,
    text="Health Tracker",
    font=("Segoe UI", 25, "bold"),
    bg=BG,
    fg=TEXT
).pack(anchor="w")

tk.Label(
    header,
    text="Your personal BMI and wellness dashboard",
    font=("Segoe UI", 11),
    bg=BG,
    fg=MUTED
).pack(anchor="w", pady=(2, 0))


# ---------------- SUMMARY CARDS ----------------

summary_frame = tk.Frame(root, bg=BG)
summary_frame.pack(fill="x", padx=24, pady=(0, 14))

summary_frame.grid_columnconfigure(0, weight=1)
summary_frame.grid_columnconfigure(1, weight=1)
summary_frame.grid_columnconfigure(2, weight=1)


def create_summary_card(column, title, initial_value="--"):
    """Create each summary card and its own child labels."""
    card = tk.Frame(
        summary_frame,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1,
        padx=16,
        pady=12
    )

    card.grid(
        row=0,
        column=column,
        sticky="nsew",
        padx=(0, 8) if column < 2 else (0, 0)
    )

    tk.Label(
        card,
        text=title,
        font=("Segoe UI", 10),
        bg=CARD,
        fg=MUTED
    ).pack(anchor="w")

    value = tk.Label(
        card,
        text=initial_value,
        font=("Segoe UI", 22, "bold"),
        bg=CARD,
        fg=PURPLE
    )
    value.pack(anchor="w", pady=(5, 0))

    return card, value


total_card, total_value = create_summary_card(
    0, "Total Records", "0"
)

average_card, average_value = create_summary_card(
    1, "Average BMI"
)

latest_card, latest_value = create_summary_card(
    2, "Latest BMI"
)

latest_category = tk.Label(
    latest_card,
    text="No records yet",
    font=("Segoe UI", 10, "bold"),
    bg=CARD,
    fg=MUTED
)
latest_category.pack(anchor="w", pady=(2, 0))


# ---------------- MAIN CONTENT ----------------

main = tk.Frame(root, bg=BG)
main.pack(fill="both", expand=True, padx=24, pady=(0, 20))

main.grid_columnconfigure(0, weight=4, uniform="main")
main.grid_columnconfigure(1, weight=6, uniform="main")
main.grid_rowconfigure(0, weight=1)


# ---------------- CALCULATOR PANEL ----------------

calculator = make_card(
    main,
    "BMI Calculator",
    "Enter your details to calculate and save BMI."
)

calculator.grid(
    row=0,
    column=0,
    sticky="nsew",
    padx=(0, 8)
)

tk.Label(
    calculator,
    text="Full name",
    font=("Segoe UI", 10, "bold"),
    bg=CARD,
    fg=TEXT
).pack(anchor="w", pady=(5, 4))

name_entry = ttk.Entry(calculator, font=("Segoe UI", 11))
name_entry.pack(fill="x", ipady=5)

tk.Label(
    calculator,
    text="Measurement units",
    font=("Segoe UI", 10, "bold"),
    bg=CARD,
    fg=TEXT
).pack(anchor="w", pady=(12, 4))

units = tk.StringVar(value="Metric (kg / cm)")

unit_combo = ttk.Combobox(
    calculator,
    textvariable=units,
    values=("Metric (kg / cm)", "Imperial (lbs / inches)"),
    state="readonly",
    font=("Segoe UI", 10)
)
unit_combo.pack(fill="x", ipady=3)
unit_combo.bind("<<ComboboxSelected>>", update_unit_labels)

weight_label = tk.Label(
    calculator,
    text="Weight (kg)",
    font=("Segoe UI", 10, "bold"),
    bg=CARD,
    fg=TEXT
)
weight_label.pack(anchor="w", pady=(12, 4))

weight_entry = ttk.Entry(calculator, font=("Segoe UI", 11))
weight_entry.pack(fill="x", ipady=5)

height_label = tk.Label(
    calculator,
    text="Height (cm)",
    font=("Segoe UI", 10, "bold"),
    bg=CARD,
    fg=TEXT
)
height_label.pack(anchor="w", pady=(12, 4))

height_entry = ttk.Entry(calculator, font=("Segoe UI", 11))
height_entry.pack(fill="x", ipady=5)

make_button(
    calculator,
    "Calculate & Save BMI",
    calculate_and_save,
    primary=True
).pack(fill="x", pady=(16, 7))

make_button(
    calculator,
    "Clear Fields",
    clear_fields
).pack(fill="x")


# ---------------- RESULT CARD ----------------

result_card = tk.Frame(
    calculator,
    bg="#F5F1FF",
    padx=12,
    pady=10
)
result_card.pack(fill="x", pady=(14, 0))

tk.Label(
    result_card,
    text="YOUR BMI",
    font=("Segoe UI", 9, "bold"),
    bg="#F5F1FF",
    fg=MUTED
).pack(anchor="w")

result_bmi = tk.Label(
    result_card,
    text="--",
    font=("Segoe UI", 26, "bold"),
    bg="#F5F1FF",
    fg=PURPLE
)
result_bmi.pack(anchor="w")

result_category = tk.Label(
    result_card,
    text="Waiting for calculation",
    font=("Segoe UI", 10, "bold"),
    bg="#F5F1FF",
    fg=MUTED
)
result_category.pack(anchor="w")

tk.Label(
    calculator,
    text="BMI is a screening measure, not a diagnosis.",
    font=("Segoe UI", 8),
    bg=CARD,
    fg=MUTED,
    wraplength=300,
    justify="left"
).pack(anchor="w", pady=(10, 0))


# ---------------- HISTORY PANEL ----------------

history_panel = make_card(
    main,
    "BMI History",
    "Saved records. Double-click a row to select its user."
)

history_panel.grid(
    row=0,
    column=1,
    sticky="nsew",
    padx=(8, 0)
)

selected_user = tk.StringVar()

toolbar = tk.Frame(history_panel, bg=CARD)
toolbar.pack(fill="x", pady=(0, 10))

user_combo = ttk.Combobox(
    toolbar,
    textvariable=selected_user,
    state="readonly",
    width=15,
    font=("Segoe UI", 9)
)
user_combo.pack(side="left", padx=(0, 6), ipady=3)

make_button(
    toolbar,
    "Show Trend",
    show_trend
).pack(side="left", padx=(0, 6))

make_button(
    toolbar,
    "Export CSV",
    export_csv
).pack(side="left")


# ---------------- HISTORY TABLE ----------------

table_frame = tk.Frame(history_panel, bg=CARD)
table_frame.pack(fill="both", expand=True)

columns = (
    "Name", "BMI", "Category",
    "Weight kg", "Height cm", "Date & Time"
)

history_tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

widths = (100, 60, 95, 85, 85, 150)

for column, width in zip(columns, widths):
    history_tree.heading(column, text=column)
    history_tree.column(
        column,
        width=width,
        minwidth=55,
        anchor="center",
        stretch=True
    )

vertical_scroll = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=history_tree.yview
)

horizontal_scroll = ttk.Scrollbar(
    table_frame,
    orient="horizontal",
    command=history_tree.xview
)

history_tree.configure(
    yscrollcommand=vertical_scroll.set,
    xscrollcommand=horizontal_scroll.set
)

history_tree.grid(row=0, column=0, sticky="nsew")
vertical_scroll.grid(row=0, column=1, sticky="ns")
horizontal_scroll.grid(row=1, column=0, sticky="ew")

table_frame.grid_rowconfigure(0, weight=1)
table_frame.grid_columnconfigure(0, weight=1)

history_tree.bind(
    "<Double-1>",
    on_history_double_click
)


# ---------------- START APPLICATION ----------------

refresh_dashboard()
name_entry.focus_set()

root.mainloop()
