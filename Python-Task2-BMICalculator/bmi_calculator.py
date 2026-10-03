import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt


# =========================
# DATABASE
# =========================

DB_NAME = "bmi_records.db"


def create_database():
    """Create the BMI records table if it does not exist."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
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

        conn.commit()
        conn.close()

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Could not create database:\n{error}"
        )


# =========================
# BMI CALCULATION
# =========================

def calculate_bmi():
    """Calculate BMI and save the record."""

    name = name_entry.get().strip()
    weight_text = weight_entry.get().strip()
    height_text = height_entry.get().strip()

    # Check name
    if not name:
        messagebox.showwarning(
            "Input Required",
            "Please enter the user's name."
        )
        return

    # Check empty fields
    if not weight_text or not height_text:
        messagebox.showwarning(
            "Input Required",
            "Please enter both weight and height."
        )
        return

    # Convert values
    try:
        weight = float(weight_text)
        height = float(height_text)

    except ValueError:
        messagebox.showerror(
            "Invalid Input",
            "Weight and height must be numeric values."
        )
        return

    # Check positive values
    if weight <= 0 or height <= 0:
        messagebox.showerror(
            "Invalid Input",
            "Weight and height must be greater than zero."
        )
        return

    # BMI formula
    bmi = weight / (height ** 2)
    bmi = round(bmi, 2)

    # BMI category
    if bmi < 18.5:
        category = "Underweight"
        result_color = "#3498db"

    elif bmi < 25:
        category = "Normal"
        result_color = "#27ae60"

    elif bmi < 30:
        category = "Overweight"
        result_color = "#f39c12"

    else:
        category = "Obese"
        result_color = "#e74c3c"

    # Display result
    result_label.config(
        text=f"BMI: {bmi}\nCategory: {category}",
        foreground=result_color
    )

    # Save record
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        recorded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO bmi_records
            (user_name, weight, height, bmi, category, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            weight,
            height,
            bmi,
            category,
            recorded_at
        ))

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Success",
            f"BMI calculated successfully!\n\n"
            f"User: {name}\n"
            f"BMI: {bmi}\n"
            f"Category: {category}"
        )

        load_users()

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Could not save BMI record:\n{error}"
        )


# =========================
# LOAD USERS
# =========================

def load_users():
    """Load unique user names into the dropdown."""

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT user_name
            FROM bmi_records
            ORDER BY user_name
        """)

        users = [row[0] for row in cursor.fetchall()]

        conn.close()

        user_combo["values"] = users

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Could not load users:\n{error}"
        )


# =========================
# SHOW HISTORY
# =========================

def show_history():
    """Display all BMI records in a new window."""

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_name, weight, height, bmi, category, recorded_at
            FROM bmi_records
            ORDER BY id DESC
        """)

        records = cursor.fetchall()
        conn.close()

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Could not read BMI history:\n{error}"
        )
        return

    if not records:
        messagebox.showinfo(
            "History",
            "No BMI records found."
        )
        return

    history_window = tk.Toplevel(root)
    history_window.title("BMI History")
    history_window.geometry("850x450")

    title = ttk.Label(
        history_window,
        text="BMI History",
        font=("Arial", 18, "bold")
    )
    title.pack(pady=10)

    columns = (
        "Name",
        "Weight",
        "Height",
        "BMI",
        "Category",
        "Date & Time"
    )

    tree = ttk.Treeview(
        history_window,
        columns=columns,
        show="headings"
    )

    for column in columns:
        tree.heading(column, text=column)
        tree.column(column, width=120)

    for record in records:
        tree.insert("", tk.END, values=record)

    tree.pack(
        fill=tk.BOTH,
        expand=True,
        padx=10,
        pady=10
    )


# =========================
# SHOW BMI TREND
# =========================

def show_trend():
    """Show BMI trend chart for the selected user."""

    selected_user = user_combo.get().strip()

    if not selected_user:
        messagebox.showwarning(
            "Select User",
            "Please select a user first."
        )
        return

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT recorded_at, bmi
            FROM bmi_records
            WHERE user_name = ?
            ORDER BY id
        """, (selected_user,))

        records = cursor.fetchall()
        conn.close()

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Could not read trend data:\n{error}"
        )
        return

    if not records:
        messagebox.showinfo(
            "No Data",
            f"No BMI records found for {selected_user}."
        )
        return

    dates = [record[0] for record in records]
    bmi_values = [record[1] for record in records]

    # Create graph
    plt.figure(figsize=(9, 5))

    plt.plot(
        dates,
        bmi_values,
        marker="o",
        linewidth=2
    )

    plt.axhline(
        y=18.5,
        linestyle="--",
        label="18.5"
    )

    plt.axhline(
        y=25,
        linestyle="--",
        label="25"
    )

    plt.axhline(
        y=30,
        linestyle="--",
        label="30"
    )

    plt.title(f"BMI Trend - {selected_user}")
    plt.xlabel("Date & Time")
    plt.ylabel("BMI")

    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.tight_layout()
    plt.show()


# =========================
# CLEAR FIELDS
# =========================

def clear_fields():
    """Clear all input fields."""

    name_entry.delete(0, tk.END)
    weight_entry.delete(0, tk.END)
    height_entry.delete(0, tk.END)

    result_label.config(
        text="BMI: --\nCategory: --",
        foreground="#333333"
    )


# =========================
# MAIN WINDOW
# =========================

create_database()

root = tk.Tk()
root.title("Advanced BMI Calculator")
root.geometry("650x650")
root.resizable(False, False)


# Main title
title_label = tk.Label(
    root,
    text="Advanced BMI Calculator",
    font=("Arial", 24, "bold")
)
title_label.pack(pady=20)


subtitle_label = tk.Label(
    root,
    text="Calculate, save and track BMI records",
    font=("Arial", 11)
)
subtitle_label.pack(pady=(0, 20))


# Input frame
input_frame = ttk.LabelFrame(
    root,
    text="Enter Details",
    padding=20
)
input_frame.pack(
    padx=40,
    fill="x"
)


# Name
ttk.Label(
    input_frame,
    text="User Name:"
).grid(
    row=0,
    column=0,
    padx=10,
    pady=10,
    sticky="w"
)

name_entry = ttk.Entry(
    input_frame,
    width=35
)
name_entry.grid(
    row=0,
    column=1,
    padx=10,
    pady=10
)


# Weight
ttk.Label(
    input_frame,
    text="Weight (kg):"
).grid(
    row=1,
    column=0,
    padx=10,
    pady=10,
    sticky="w"
)

weight_entry = ttk.Entry(
    input_frame,
    width=35
)
weight_entry.grid(
    row=1,
    column=1,
    padx=10,
    pady=10
)


# Height
ttk.Label(
    input_frame,
    text="Height (m):"
).grid(
    row=2,
    column=0,
    padx=10,
    pady=10,
    sticky="w"
)

height_entry = ttk.Entry(
    input_frame,
    width=35
)
height_entry.grid(
    row=2,
    column=1,
    padx=10,
    pady=10
)


# Calculate button
calculate_button = ttk.Button(
    root,
    text="Calculate BMI",
    command=calculate_bmi
)
calculate_button.pack(pady=20)


# Result
result_label = tk.Label(
    root,
    text="BMI: --\nCategory: --",
    font=("Arial", 18, "bold")
)
result_label.pack(pady=10)


# User selection frame
user_frame = ttk.LabelFrame(
    root,
    text="BMI Trend",
    padding=15
)
user_frame.pack(
    padx=40,
    pady=15,
    fill="x"
)


ttk.Label(
    user_frame,
    text="Select User:"
).pack(
    side="left",
    padx=10
)


user_combo = ttk.Combobox(
    user_frame,
    width=25,
    state="readonly"
)
user_combo.pack(
    side="left",
    padx=10
)


trend_button = ttk.Button(
    user_frame,
    text="Show Trend",
    command=show_trend
)
trend_button.pack(
    side="left",
    padx=10
)


# Bottom buttons
button_frame = ttk.Frame(root)
button_frame.pack(pady=20)


history_button = ttk.Button(
    button_frame,
    text="View History",
    command=show_history
)
history_button.grid(
    row=0,
    column=0,
    padx=10
)


clear_button = ttk.Button(
    button_frame,
    text="Clear",
    command=clear_fields
)
clear_button.grid(
    row=0,
    column=1,
    padx=10
)


exit_button = ttk.Button(
    button_frame,
    text="Exit",
    command=root.destroy
)
exit_button.grid(
    row=0,
    column=2,
    padx=10
)


# Load existing users
load_users()


# Start application
root.mainloop()
