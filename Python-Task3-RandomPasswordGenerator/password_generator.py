import tkinter as tk
from tkinter import ttk, messagebox
import secrets
import string
import pyperclip


# =========================
# SETTINGS
# =========================

AMBIGUOUS_CHARACTERS = "0Ol1I"


# =========================
# PASSWORD GENERATOR
# =========================

def generate_password():
    """Generate a secure password based on selected options."""

    try:
        length = int(length_var.get())
    except ValueError:
        messagebox.showerror("Invalid Length", "Please enter a valid password length.")
        return

    if length < 8:
        messagebox.showerror(
            "Invalid Length",
            "Password length must be at least 8 characters."
        )
        return

    selected_sets = []

    if uppercase_var.get():
        selected_sets.append(string.ascii_uppercase)

    if lowercase_var.get():
        selected_sets.append(string.ascii_lowercase)

    if numbers_var.get():
        selected_sets.append(string.digits)

    if symbols_var.get():
        selected_sets.append(string.punctuation)

    if len(selected_sets) < 2:
        messagebox.showwarning(
            "Character Types Required",
            "Please select at least 2 character types."
        )
        return

    # Remove ambiguous characters if requested
    if exclude_ambiguous_var.get():
        selected_sets = [
            "".join(
                char for char in character_set
                if char not in AMBIGUOUS_CHARACTERS
            )
            for character_set in selected_sets
        ]

    # Make sure no selected set became empty
    selected_sets = [character_set for character_set in selected_sets if character_set]

    if len(selected_sets) < 2:
        messagebox.showwarning(
            "Invalid Selection",
            "The selected character types do not contain enough characters."
        )
        return

    # Guarantee at least one character from every selected type
    password_characters = [
        secrets.choice(character_set)
        for character_set in selected_sets
    ]

    # Create combined character pool
    all_characters = "".join(selected_sets)

    remaining_length = length - len(password_characters)

    for _ in range(remaining_length):
        password_characters.append(
            secrets.choice(all_characters)
        )

    # Cryptographically secure shuffle
    secrets.SystemRandom().shuffle(password_characters)

    password = "".join(password_characters)

    # Display password
    password_var.set(password)

    # Calculate and display strength
    strength, strength_value = calculate_strength(
        length,
        len(selected_sets)
    )

    strength_var.set(f"Strength: {strength}")
    strength_bar["value"] = strength_value

    # Automatically copy password
    try:
        pyperclip.copy(password)
        clipboard_var.set("✓ Password copied to clipboard")
    except Exception:
        clipboard_var.set("Clipboard copy failed")

    # Add to session history
    add_to_history(password)


# =========================
# PASSWORD STRENGTH
# =========================

def calculate_strength(length, character_type_count):
    """Return password strength and progress value."""

    if length >= 16 and character_type_count >= 4:
        return "Strong", 100

    elif length >= 12 and character_type_count >= 3:
        return "Strong", 100

    elif length >= 10 and character_type_count >= 2:
        return "Medium", 60

    else:
        return "Weak", 30


# =========================
# HISTORY
# =========================

password_history = []


def add_to_history(password):
    """Store only the last five generated passwords in memory."""

    password_history.insert(0, password)

    if len(password_history) > 5:
        password_history.pop()

    update_history_display()


def update_history_display():
    """Update the session history list."""

    history_listbox.delete(0, tk.END)

    for index, password in enumerate(password_history, start=1):
        history_listbox.insert(
            tk.END,
            f"{index}. {password}"
        )


def copy_selected_password():
    """Copy selected history password to clipboard."""

    selection = history_listbox.curselection()

    if not selection:
        messagebox.showinfo(
            "Select Password",
            "Please select a password from the history first."
        )
        return

    selected_index = selection[0]
    password = password_history[selected_index]

    try:
        pyperclip.copy(password)
        clipboard_var.set("✓ Selected password copied to clipboard")

    except Exception:
        messagebox.showerror(
            "Clipboard Error",
            "Could not copy the password to clipboard."
        )


# =========================
# CLEAR
# =========================

def clear_password():
    """Clear the current password and status."""

    password_var.set("")
    strength_var.set("Strength: --")
    strength_bar["value"] = 0
    clipboard_var.set("")


# =========================
# MAIN WINDOW
# =========================

root = tk.Tk()

root.title("Advanced Random Password Generator")
root.geometry("720x720")
root.resizable(False, False)


# =========================
# TITLE
# =========================

title_label = tk.Label(
    root,
    text="🔐 Advanced Random Password Generator",
    font=("Arial", 22, "bold")
)

title_label.pack(pady=(20, 5))


subtitle_label = tk.Label(
    root,
    text="Generate strong and cryptographically secure passwords",
    font=("Arial", 10)
)

subtitle_label.pack(pady=(0, 20))


# =========================
# LENGTH
# =========================

length_frame = ttk.LabelFrame(
    root,
    text="Password Length",
    padding=15
)

length_frame.pack(
    padx=40,
    fill="x"
)


ttk.Label(
    length_frame,
    text="Length:"
).grid(
    row=0,
    column=0,
    padx=10
)


length_var = tk.IntVar(value=16)


length_spinbox = tk.Spinbox(
    length_frame,
    from_=8,
    to=128,
    textvariable=length_var,
    width=10
)

length_spinbox.grid(
    row=0,
    column=1,
    padx=10
)


ttk.Label(
    length_frame,
    text="Minimum: 8 characters"
).grid(
    row=0,
    column=2,
    padx=10
)


# =========================
# CHARACTER TYPES
# =========================

types_frame = ttk.LabelFrame(
    root,
    text="Character Types",
    padding=15
)

types_frame.pack(
    padx=40,
    pady=15,
    fill="x"
)


uppercase_var = tk.BooleanVar(value=True)
lowercase_var = tk.BooleanVar(value=True)
numbers_var = tk.BooleanVar(value=True)
symbols_var = tk.BooleanVar(value=True)


ttk.Checkbutton(
    types_frame,
    text="Uppercase (A-Z)",
    variable=uppercase_var
).grid(
    row=0,
    column=0,
    padx=10,
    pady=5,
    sticky="w"
)


ttk.Checkbutton(
    types_frame,
    text="Lowercase (a-z)",
    variable=lowercase_var
).grid(
    row=0,
    column=1,
    padx=10,
    pady=5,
    sticky="w"
)


ttk.Checkbutton(
    types_frame,
    text="Numbers (0-9)",
    variable=numbers_var
).grid(
    row=1,
    column=0,
    padx=10,
    pady=5,
    sticky="w"
)


ttk.Checkbutton(
    types_frame,
    text="Symbols (!@#$)",
    variable=symbols_var
).grid(
    row=1,
    column=1,
    padx=10,
    pady=5,
    sticky="w"
)


# =========================
# SECURITY OPTIONS
# =========================

security_frame = ttk.LabelFrame(
    root,
    text="Security Options",
    padding=15
)

security_frame.pack(
    padx=40,
    pady=5,
    fill="x"
)


exclude_ambiguous_var = tk.BooleanVar(value=False)


ttk.Checkbutton(
    security_frame,
    text="Exclude ambiguous characters (0, O, l, 1, I)",
    variable=exclude_ambiguous_var
).pack(anchor="w")


# =========================
# GENERATE BUTTON
# =========================

generate_button = ttk.Button(
    root,
    text="Generate Secure Password",
    command=generate_password
)

generate_button.pack(
    pady=20
)


# =========================
# PASSWORD DISPLAY
# =========================

password_frame = ttk.LabelFrame(
    root,
    text="Generated Password",
    padding=15
)

password_frame.pack(
    padx=40,
    fill="x"
)


password_var = tk.StringVar()


password_entry = ttk.Entry(
    password_frame,
    textvariable=password_var,
    font=("Consolas", 14),
    justify="center",
    state="readonly",
    width=55
)

password_entry.pack(
    pady=5
)


# =========================
# STRENGTH
# =========================

strength_var = tk.StringVar(
    value="Strength: --"
)


strength_label = ttk.Label(
    root,
    textvariable=strength_var,
    font=("Arial", 13, "bold")
)

strength_label.pack(
    pady=(15, 5)
)


strength_bar = ttk.Progressbar(
    root,
    orient="horizontal",
    length=400,
    mode="determinate",
    maximum=100
)

strength_bar.pack(
    pady=5
)


# =========================
# CLIPBOARD STATUS
# =========================

clipboard_var = tk.StringVar()


clipboard_label = ttk.Label(
    root,
    textvariable=clipboard_var
)

clipboard_label.pack(
    pady=5
)


# =========================
# HISTORY
# =========================

history_frame = ttk.LabelFrame(
    root,
    text="Last 5 Generated Passwords (Session Only)",
    padding=10
)

history_frame.pack(
    padx=40,
    pady=15,
    fill="both",
    expand=True
)


history_listbox = tk.Listbox(
    history_frame,
    height=5,
    font=("Consolas", 10)
)

history_listbox.pack(
    side="left",
    fill="both",
    expand=True,
    padx=5
)


history_scrollbar = ttk.Scrollbar(
    history_frame,
    orient="vertical",
    command=history_listbox.yview
)

history_scrollbar.pack(
    side="right",
    fill="y"
)


history_listbox.config(
    yscrollcommand=history_scrollbar.set
)


# =========================
# BOTTOM BUTTONS
# =========================

button_frame = ttk.Frame(root)

button_frame.pack(
    pady=15
)


copy_button = ttk.Button(
    button_frame,
    text="Copy Selected",
    command=copy_selected_password
)

copy_button.grid(
    row=0,
    column=0,
    padx=8
)


clear_button = ttk.Button(
    button_frame,
    text="Clear",
    command=clear_password
)

clear_button.grid(
    row=0,
    column=1,
    padx=8
)


exit_button = ttk.Button(
    button_frame,
    text="Exit",
    command=root.destroy
)

exit_button.grid(
    row=0,
    column=2,
    padx=8
)


# =========================
# START APPLICATION
# =========================

root.mainloop()