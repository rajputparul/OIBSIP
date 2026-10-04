\# Random Password Generator



\## Oasis Infobyte Python Programming Internship – Task 3



A secure Random Password Generator developed in Python using Tkinter GUI.



The application generates strong random passwords based on user-selected criteria such as password length and character types.



\## Features



\- User-friendly Tkinter GUI

\- Password length selection from 8 to 128 characters

\- Uppercase letters

\- Lowercase letters

\- Numbers

\- Symbols

\- Uses Python's `secrets` module for secure password generation

\- Excludes ambiguous characters such as `0`, `O`, `l`, `1`, and `I`

\- Guarantees at least one character from every selected character type

\- Password strength indicator:

&#x20; - Weak

&#x20; - Medium

&#x20; - Strong

\- Automatically copies generated password to clipboard

\- Manual Copy button

\- Displays the last 5 generated passwords during the current session

\- Password history is not stored permanently

\- Clear and Exit options



\## Technologies Used



\- Python

\- Tkinter

\- secrets

\- pyperclip



\## How to Run



1\. Make sure Python is installed.

2\. Install the required package:



```bash

python -m pip install pyperclip

