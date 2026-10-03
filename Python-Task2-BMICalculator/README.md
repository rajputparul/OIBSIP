\# Advanced BMI Calculator



\## Oasis Infobyte Internship - Python Programming



\### Task 2: BMI Calculator



An advanced BMI Calculator developed using Python. The application provides a graphical user interface, calculates BMI, classifies the result, stores multiple users' records in SQLite, and displays BMI trends using Matplotlib.



\---



\## Features



\- Calculate BMI using weight and height

\- Graphical User Interface using Tkinter

\- BMI classification:

&#x20; - Underweight

&#x20; - Normal

&#x20; - Overweight

&#x20; - Obese

\- Colour-coded BMI results

\- Input validation for invalid and negative values

\- Support for multiple users

\- Store BMI records using SQLite

\- View complete BMI history

\- Select a user and view their BMI trend

\- BMI trend visualization using Matplotlib

\- Database error handling

\- Clear input fields

\- Exit option



\---



\## Technologies Used



\- Python

\- Tkinter

\- SQLite

\- Matplotlib

\- Datetime



\---



\## BMI Formula



The application calculates BMI using:



BMI = Weight (kg) / Height² (m)



\### Example



Weight = 60 kg  

Height = 1.65 m



BMI = 60 / (1.65 × 1.65)



BMI ≈ 22.04



\---



\## BMI Categories



| BMI Range | Category |

|-----------|----------|

| Below 18.5 | Underweight |

| 18.5 - 24.9 | Normal |

| 25 - 29.9 | Overweight |

| 30 and above | Obese |



\---



\## Project Structure



```text

Python-Task2-BMICalculator/

│

├── bmi\_calculator.py

├── bmi\_records.db

└── README.md

