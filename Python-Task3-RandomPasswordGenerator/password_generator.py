
import tkinter as tk
from tkinter import messagebox
import pyperclip

from password_engine import (
    PasswordOptions,
    generate_password as create_secure_password,
    estimate_entropy_bits,
    strength_label as get_strength_label,
)

# =========================
# VYPR — PASSWORD STUDIO
# =========================

BG = "#0B0E13"
PANEL = "#121720"
FIELD = "#191F29"
BORDER = "#303B49"
WHITE = "#F4F7FB"
MUTED = "#98A3B3"
RED = "#F04444"
RED_DARK = "#641B20"
GREEN = "#00E58B"
GREEN_DARK = "#173D32"
FONT = "Segoe UI"

root = tk.Tk()
root.title("VYPR | Password Studio")
root.geometry("800x850")
root.minsize(700, 760)
root.configure(bg=BG)

length_var = tk.IntVar(value=16)
uppercase_var = tk.BooleanVar(value=True)
lowercase_var = tk.BooleanVar(value=True)
numbers_var = tk.BooleanVar(value=True)
symbols_var = tk.BooleanVar(value=True)
exclude_ambiguous_var = tk.BooleanVar(value=False)

password_var = tk.StringVar(value="")
strength_var = tk.StringVar(value="WAITING FOR GENERATION")
status_var = tk.StringVar(value="Your security starts here")

history = []


def make_label(parent, text, size=11, color=WHITE, bold=False):
    return tk.Label(
        parent,
        text=text,
        bg=parent.cget("bg"),
        fg=color,
        font=(FONT, size, "bold" if bold else "normal"),
    )


def make_panel(parent, title):
    panel = tk.Frame(
        parent,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    tk.Label(
        panel,
        text=title.upper(),
        bg=PANEL,
        fg=MUTED,
        font=(FONT, 9, "bold"),
    ).pack(anchor="w", padx=16, pady=(12, 5))
    return panel


def generate_password():
    try:
        options = PasswordOptions(
            length=int(length_var.get()),
            uppercase=uppercase_var.get(),
            lowercase=lowercase_var.get(),
            digits=numbers_var.get(),
            symbols=symbols_var.get(),
            exclude_ambiguous=exclude_ambiguous_var.get(),
        )
        password = create_secure_password(options)

    except (ValueError, TypeError) as error:
        messagebox.showerror("Check your options", str(error))
        return

    password_var.set(password)

    entropy = estimate_entropy_bits(options)
    strength = get_strength_label(entropy)

    strength_var.set(f"{strength.upper()}  •  ESTIMATED {entropy:.0f} BITS")

    levels = {"Low": 1, "Moderate": 2, "Good": 4, "High": 5}
    update_strength(levels[strength])

    try:
        pyperclip.copy(password)
        status_var.set("✓  Password copied to clipboard")
    except Exception:
        status_var.set("Password generated • Clipboard copy unavailable")

    history.insert(0, password)
    del history[5:]
    refresh_history()


def update_strength(level):
    for i, segment in enumerate(strength_segments):
        segment.configure(bg=GREEN if i < level else FIELD)


def copy_password():
    password = password_var.get()
    if not password:
        status_var.set("Generate a password first")
        return
    try:
        pyperclip.copy(password)
        status_var.set("✓  Password copied to clipboard")
    except Exception:
        status_var.set("Clipboard copy unavailable")


def copy_selected():
    selection = history_list.curselection()
    if not selection:
        status_var.set("Select a password from history first")
        return
    try:
        pyperclip.copy(history[selection[0]])
        status_var.set("✓  Selected password copied")
    except Exception:
        status_var.set("Clipboard copy unavailable")


def clear_password():
    password_var.set("")
    strength_var.set("WAITING FOR GENERATION")
    status_var.set("Display cleared")
    update_strength(0)


def refresh_history():
    history_list.delete(0, tk.END)
    for i, password in enumerate(history, 1):
        history_list.insert(tk.END, f"  {i:02d}   {password}")


def toggle(parent, text, variable):
    row = tk.Frame(parent, bg=PANEL)
    row.pack(fill="x", padx=16, pady=5)

    tk.Label(
        row, text=text, bg=PANEL, fg=WHITE,
        font=(FONT, 10),
    ).pack(side="left")

    widget = tk.Checkbutton(
        row,
        variable=variable,
        text="ON",
        indicatoron=False,
        width=5,
        bg=GREEN_DARK if variable.get() else FIELD,
        fg=GREEN if variable.get() else MUTED,
        selectcolor=GREEN_DARK,
        activebackground=GREEN_DARK,
        activeforeground=GREEN,
        relief="flat",
        bd=0,
        font=(FONT, 9, "bold"),
        command=lambda: widget.configure(
            text="ON" if variable.get() else "OFF",
            bg=GREEN_DARK if variable.get() else FIELD,
            fg=GREEN if variable.get() else MUTED,
        ),
    )
    widget.pack(side="right")


# =========================
# HEADER
# =========================

header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=34, pady=(25, 18))

brand = tk.Frame(header, bg=BG)
brand.pack(anchor="w")

tk.Label(
    brand,
    text="⬡",
    font=(FONT, 34, "bold"),
    bg=BG,
    fg=RED,
).pack(side="left", padx=(0, 10))

tk.Label(
    brand,
    text="VYPR",
    font=(FONT, 26, "bold"),
    bg=BG,
    fg=WHITE,
).pack(side="left")

tk.Label(
    header,
    text="PASSWORD STUDIO     /     GENERATE • PROTECT • CONTROL",
    font=(FONT, 9),
    bg=BG,
    fg=MUTED,
).pack(anchor="w", padx=(3, 0), pady=(2, 0))


# =========================
# PASSWORD DISPLAY
# =========================

display = tk.Frame(
    root, bg=PANEL,
    highlightbackground=BORDER,
    highlightthickness=1,
)
display.pack(fill="x", padx=34, pady=5)

topline = tk.Frame(display, bg=PANEL)
topline.pack(fill="x", padx=18, pady=(15, 5))

tk.Label(
    topline, text="YOUR NEW PASSWORD",
    bg=PANEL, fg=MUTED,
    font=(FONT, 9, "bold"),
).pack(side="left")

tk.Label(
    topline, text="● SECURE GENERATOR",
    bg=PANEL, fg=GREEN,
    font=(FONT, 8, "bold"),
).pack(side="right")

password_row = tk.Frame(
    display, bg=FIELD,
    highlightbackground=BORDER,
    highlightthickness=1,
)
password_row.pack(fill="x", padx=16, pady=(4, 15))

password_entry = tk.Entry(
    password_row,
    textvariable=password_var,
    bg=FIELD,
    fg=WHITE,
    insertbackground=WHITE,
    readonlybackground=FIELD,
    relief="flat",
    font=("Consolas", 20, "bold"),
    justify="center",
    state="readonly",
)
password_entry.pack(
    side="left", fill="x", expand=True,
    ipady=13, padx=(10, 0),
)

tk.Button(
    password_row,
    text="COPY",
    command=copy_password,
    bg=FIELD,
    fg=GREEN,
    activebackground=FIELD,
    activeforeground=WHITE,
    relief="flat",
    bd=0,
    font=(FONT, 10, "bold"),
    cursor="hand2",
).pack(side="right", padx=12)


# =========================
# STRENGTH METER
# =========================

strength_panel = tk.Frame(root, bg=BG)
strength_panel.pack(fill="x", padx=36, pady=(14, 10))

strength_header = tk.Frame(strength_panel, bg=BG)
strength_header.pack(fill="x")

tk.Label(
    strength_header,
    text="PASSWORD STRENGTH",
    bg=BG,
    fg=WHITE,
    font=(FONT, 10, "bold"),
).pack(side="left")

tk.Label(
    strength_header,
    textvariable=strength_var,
    bg=BG,
    fg=GREEN,
    font=(FONT, 9, "bold"),
).pack(side="right")

meter = tk.Frame(
    strength_panel, bg=FIELD,
    highlightbackground=BORDER,
    highlightthickness=1,
)
meter.pack(fill="x", pady=8, ipady=3)

strength_segments = []
for i in range(5):
    segment = tk.Frame(meter, bg=FIELD, height=12)
    segment.pack(
        side="left", fill="x", expand=True,
        padx=(4 if i == 0 else 2, 2), pady=4,
    )
    strength_segments.append(segment)


# =========================
# OPTIONS
# =========================

options_panel = make_panel(root, "Customize your password")
options_panel.pack(fill="x", padx=34, pady=(8, 10))

length_row = tk.Frame(options_panel, bg=PANEL)
length_row.pack(fill="x", padx=16, pady=(10, 5))

tk.Label(
    length_row, text="Password length",
    bg=PANEL, fg=WHITE,
    font=(FONT, 11),
).pack(side="left")

length_value = tk.Label(
    length_row, text="16 characters",
    bg=PANEL, fg=WHITE,
    font=(FONT, 11, "bold"),
)
length_value.pack(side="right")


def on_length_change(value):
    length_value.configure(text=f"{int(float(value))} characters")


length_slider = tk.Scale(
    options_panel,
    from_=8,
    to=128,
    resolution=1,
    orient="horizontal",
    variable=length_var,
    command=on_length_change,
    bg=PANEL,
    fg=RED,
    troughcolor="#343B46",
    activebackground=RED,
    highlightthickness=0,
    bd=0,
    showvalue=False,
    sliderlength=18,
)
length_slider.pack(fill="x", padx=12, pady=(0, 10))


columns = tk.Frame(options_panel, bg=PANEL)
columns.pack(fill="x", padx=8, pady=(0, 10))

left_options = tk.Frame(columns, bg=PANEL)
left_options.pack(side="left", fill="x", expand=True)

right_options = tk.Frame(columns, bg=PANEL)
right_options.pack(side="left", fill="x", expand=True)

toggle(left_options, "Uppercase (A-Z)", uppercase_var)
toggle(left_options, "Lowercase (a-z)", lowercase_var)
toggle(right_options, "Numbers (0-9)", numbers_var)
toggle(right_options, "Symbols (!@#$)", symbols_var)


# =========================
# SECURITY OPTION
# =========================

security_panel = make_panel(root, "Security")
security_panel.pack(fill="x", padx=34, pady=(0, 12))

tk.Checkbutton(
    security_panel,
    text="Exclude ambiguous characters   (0, O, l, 1, I)",
    variable=exclude_ambiguous_var,
    bg=PANEL,
    fg=WHITE,
    selectcolor=FIELD,
    activebackground=PANEL,
    activeforeground=GREEN,
    font=(FONT, 10),
    relief="flat",
    bd=0,
).pack(anchor="w", padx=16, pady=(4, 14))


# =========================
# GENERATE ACTION
# =========================

generate_button = tk.Button(
    root,
    text="GENERATE NEW PASSWORD   →",
    command=generate_password,
    bg=RED_DARK,
    fg=WHITE,
    activebackground=RED,
    activeforeground=WHITE,
    relief="flat",
    bd=0,
    font=(FONT, 13, "bold"),
    cursor="hand2",
)
generate_button.pack(fill="x", padx=34, ipady=14, pady=(2, 12))


# =========================
# STATUS AND HISTORY
# =========================

tk.Label(
    root,
    textvariable=status_var,
    bg=BG,
    fg=GREEN,
    font=(FONT, 9),
).pack(anchor="w", padx=38, pady=(0, 7))

history_panel = make_panel(root, "Recent passwords • Current session only")
history_panel.pack(fill="both", expand=True, padx=34, pady=(0, 10))

history_list = tk.Listbox(
    history_panel,
    height=4,
    bg=FIELD,
    fg=WHITE,
    selectbackground=RED_DARK,
    selectforeground=WHITE,
    font=("Consolas", 10),
    relief="flat",
    highlightthickness=0,
    activestyle="none",
)
history_list.pack(
    fill="both", expand=True,
    padx=12, pady=(5, 8),
)

bottom = tk.Frame(root, bg=BG)
bottom.pack(fill="x", padx=34, pady=(0, 15))

tk.Button(
    bottom, text="COPY SELECTED",
    command=copy_selected,
    bg=FIELD, fg=WHITE,
    activebackground=BORDER,
    activeforeground=WHITE,
    relief="flat", bd=0,
    font=(FONT, 9, "bold"),
).pack(side="left", ipady=7, ipadx=8)

tk.Button(
    bottom, text="CLEAR DISPLAY",
    command=clear_password,
    bg=FIELD, fg=MUTED,
    activebackground=BORDER,
    activeforeground=WHITE,
    relief="flat", bd=0,
    font=(FONT, 9, "bold"),
).pack(side="left", padx=8, ipady=7, ipadx=8)

tk.Button(
    bottom, text="EXIT",
    command=root.destroy,
    bg=BG, fg=RED,
    activebackground=BG,
    activeforeground=WHITE,
    relief="flat", bd=0,
    font=(FONT, 9, "bold"),
).pack(side="right", ipady=7, ipadx=8)


if __name__ == "__main__":
    root.mainloop()
