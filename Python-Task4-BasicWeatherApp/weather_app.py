
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from collections import defaultdict

import requests
from dotenv import load_dotenv

# =========================================================
# CLIMA WEATHER DASHBOARD
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()

CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

ORANGE = "#FFA526"
TEAL = "#176F7B"
TEAL_DARK = "#115B68"
CREAM = "#F2EAE1"
WHITE = "#FFFFFF"
TEXT = "#276B7A"
MUTED = "#78919A"
BORDER = "#E9E1DA"
PURPLE = "#7257E8"

WEATHER_ICONS = {
    "clear": "☀",
    "cloud": "☁",
    "rain": "🌧",
    "drizzle": "🌦",
    "thunder": "⛈",
    "snow": "❄",
    "mist": "🌫",
    "fog": "🌫",
    "haze": "🌫",
    "smoke": "🌫",
}

def icon_for(condition):
    condition = str(condition).lower()
    for key, value in WEATHER_ICONS.items():
        if key in condition:
            return value
    return "🌤"

def temp_text(value, unit="metric"):
    return f"{round(value)}°{'C' if unit == 'metric' else 'F'}"


class ClimaDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("CLIMA | Weather Intelligence")
        self.root.geometry("1280x800")
        self.root.minsize(1050, 720)
        self.root.configure(bg=ORANGE)

        self.unit = "metric"
        self.city = "London"
        self.busy = False
        self.request_number = 0
        self.current_data = None
        self.forecast_data = None

        self.build_layout()
        self.root.after(300, self.load_default_city)

    # =====================================================
    # UI HELPERS
    # =====================================================

    def label(
        self, parent, text, size=10, color=TEXT,
        bold=False, bg=WHITE, anchor="w"
    ):
        return tk.Label(
            parent,
            text=text,
            font=("Segoe UI", size, "bold" if bold else "normal"),
            fg=color,
            bg=bg,
            anchor=anchor
        )

    def card(self, parent, padding=12, bg=WHITE):
        return tk.Frame(
            parent,
            bg=bg,
            padx=padding,
            pady=padding,
            highlightbackground=BORDER,
            highlightthickness=1
        )

    def button(self, parent, text, command, bg=TEAL, fg=WHITE):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=TEAL_DARK,
            activeforeground=WHITE,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2"
        )

    # =====================================================
    # MAIN LAYOUT
    # =====================================================

    def build_layout(self):
        outer = tk.Frame(self.root, bg=ORANGE, padx=20, pady=16)
        outer.pack(fill="both", expand=True)

        # App surface
        self.surface = tk.Frame(outer, bg=CREAM)
        self.surface.pack(fill="both", expand=True)

        self.surface.grid_columnconfigure(1, weight=1)
        self.surface.grid_rowconfigure(0, weight=1)

        # Left navigation sidebar
        self.sidebar = tk.Frame(
            self.surface,
            bg=TEAL,
            width=150,
            padx=12,
            pady=18
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        self.label(
            self.sidebar, "☀", 25, WHITE, True, TEAL, "center"
        ).pack(fill="x", pady=(2, 0))

        self.label(
            self.sidebar, "CLIMA", 14, WHITE, True, TEAL, "center"
        ).pack(fill="x", pady=(0, 24))

        self.nav_buttons = {}
        for name, symbol in [
            ("Overview", "▦"),
            ("Forecasts", "☼"),
            ("Detailing", "⌁"),
            ("Alerts", "♟"),
            ("Settings", "⚙"),
        ]:
            btn = tk.Button(
                self.sidebar,
                text=f"{symbol}  {name}",
                anchor="w",
                bg=TEAL,
                fg="#D8EEF0",
                activebackground=TEAL_DARK,
                activeforeground=WHITE,
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                bd=0,
                padx=7,
                pady=10,
                cursor="hand2",
                command=lambda n=name: self.navigate(n)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[name] = btn

        self.nav_buttons["Overview"].config(fg=ORANGE)

        tk.Frame(self.sidebar, bg=TEAL).pack(fill="both", expand=True)

        self.label(
            self.sidebar, "●  Live weather", 8, "#D8EEF0",
            False, TEAL
        ).pack(anchor="w", pady=(8, 2))

        self.label(
            self.sidebar, "Powered by OpenWeather", 7, "#C4E0E3",
            False, TEAL
        ).pack(anchor="w", pady=(0, 8))

        # Main content
        self.content = tk.Frame(
            self.surface, bg=CREAM, padx=18, pady=14
        )
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        self.build_top_bar()
        self.build_current_weather()
        self.build_bottom_panels()

    def navigate(self, name):
        for key, btn in self.nav_buttons.items():
            btn.config(fg=ORANGE if key == name else "#D8EEF0")

        if name == "Forecasts":
            self.status.config(text="Forecasts update after a city search.")
        elif name == "Detailing":
            self.status.config(text="Detailed weather metrics are shown below.")
        elif name == "Alerts":
            self.status.config(text="Weather alerts depend on API availability.")
        elif name == "Settings":
            self.toggle_unit()
        else:
            self.status.config(text="Weather overview")

    # =====================================================
    # TOP BAR AND SEARCH
    # =====================================================

    def build_top_bar(self):
        top = tk.Frame(self.content, bg=CREAM)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(0, weight=1)

        self.search_entry = ttk.Entry(top, font=("Segoe UI", 10))
        self.search_entry.insert(0, self.city)
        self.search_entry.grid(row=0, column=0, sticky="ew", ipady=7)

        self.search_entry.bind(
            "<Return>", lambda _event: self.search_weather()
        )

        self.button(
            top, "Search", self.search_weather, TEAL
        ).grid(row=0, column=1, padx=(7, 4), sticky="ns")

        self.unit_button = self.button(
            top, "°C / °F", self.toggle_unit, WHITE, TEAL
        )
        self.unit_button.grid(row=0, column=2, padx=(4, 0), sticky="ns")

        self.status = self.label(
            self.content,
            "Connecting to weather service...",
            8,
            MUTED,
            False,
            CREAM
        )
        self.status.grid(row=1, column=0, sticky="w", pady=(0, 7))

    # =====================================================
    # CURRENT WEATHER AND GRAPH
    # =====================================================

    def build_current_weather(self):
        row = tk.Frame(self.content, bg=CREAM)
        row.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        row.grid_columnconfigure(0, weight=5, uniform="current")
        row.grid_columnconfigure(1, weight=4, uniform="current")
        row.grid_rowconfigure(0, weight=1)

        self.current_card = self.card(row, 14)
        self.current_card.grid(
            row=0, column=0, sticky="nsew", padx=(0, 6)
        )

        self.label(
            self.current_card, "Current conditions", 12, TEXT, True
        ).pack(anchor="w")

        self.location_label = self.label(
            self.current_card, "Search for a city", 9, MUTED
        )
        self.location_label.pack(anchor="w", pady=(3, 0))

        hero = tk.Frame(self.current_card, bg=WHITE)
        hero.pack(fill="x", pady=(10, 8))

        self.weather_icon = self.label(
            hero, "☀", 43, ORANGE, True
        )
        self.weather_icon.pack(side="left", padx=(0, 10))

        temp_frame = tk.Frame(hero, bg=WHITE)
        temp_frame.pack(side="left", fill="x", expand=True)

        self.temperature = self.label(
            temp_frame, "--°", 30, TEXT, True
        )
        self.temperature.pack(anchor="w")

        self.condition = self.label(
            temp_frame, "Waiting for weather", 10, MUTED
        )
        self.condition.pack(anchor="w")

        self.feels = self.label(
            temp_frame, "Feels like --", 8, MUTED
        )
        self.feels.pack(anchor="w", pady=(4, 0))

        self.metric_row = tk.Frame(self.current_card, bg=WHITE)
        self.metric_row.pack(fill="x", pady=(7, 0))

        self.metric_labels = {}
        metrics = [
            ("Humidity", "humidity"),
            ("Wind", "wind"),
            ("Pressure", "pressure"),
            ("Feels like", "feels"),
        ]

        for index, (title, key) in enumerate(metrics):
            self.metric_row.grid_columnconfigure(index, weight=1)

            cell = tk.Frame(
                self.metric_row, bg="#EAF4F5", padx=6, pady=9
            )
            cell.grid(
                row=0, column=index, sticky="nsew",
                padx=(0, 4) if index < 3 else (0, 0)
            )

            self.label(
                cell, title, 8, MUTED, False, "#EAF4F5"
            ).pack(anchor="center")

            value = self.label(
                cell, "--", 10, TEAL, True, "#EAF4F5"
            )
            value.pack(anchor="center", pady=(5, 0))
            self.metric_labels[key] = value

        # Temperature chart
        self.chart_card = self.card(row, 12)
        self.chart_card.grid(
            row=0, column=1, sticky="nsew", padx=(6, 0)
        )

        chart_head = tk.Frame(self.chart_card, bg=WHITE)
        chart_head.pack(fill="x")

        self.label(
            chart_head, "Temperature trend", 11, TEXT, True
        ).pack(side="left")

        self.label(
            chart_head, "5 DAYS", 8, MUTED
        ).pack(side="right")

        self.chart = tk.Canvas(
            self.chart_card,
            height=185,
            bg=WHITE,
            highlightthickness=0
        )
        self.chart.pack(fill="both", expand=True, pady=(8, 0))
        self.chart.bind("<Configure>", self.draw_chart)

    # =====================================================
    # BOTTOM PANELS
    # =====================================================

    def build_bottom_panels(self):
        bottom = tk.Frame(self.content, bg=CREAM)
        bottom.grid(row=3, column=0, sticky="nsew")
        bottom.grid_columnconfigure(0, weight=1, uniform="bottom")
        bottom.grid_columnconfigure(1, weight=1, uniform="bottom")

        # Hourly forecast
        hourly_card = self.card(bottom, 10)
        hourly_card.grid(
            row=0, column=0, sticky="nsew", padx=(0, 6)
        )

        self.label(
            hourly_card, "Hourly forecast", 11, TEXT, True
        ).pack(anchor="w")

        self.hourly_frame = tk.Frame(hourly_card, bg=WHITE)
        self.hourly_frame.pack(fill="x", pady=(8, 0))

        # Weekly forecast and precipitation
        right = tk.Frame(bottom, bg=CREAM)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.grid_columnconfigure(0, weight=1)

        weekly_card = self.card(right, 10)
        weekly_card.pack(fill="both", expand=True)

        self.label(
            weekly_card, "Weekly forecast", 11, TEXT, True
        ).pack(anchor="w")

        self.weekly_frame = tk.Frame(weekly_card, bg=WHITE)
        self.weekly_frame.pack(fill="x", pady=(7, 0))

        precip_card = self.card(right, 10)
        precip_card.pack(fill="both", expand=True, pady=(8, 0))

        self.label(
            precip_card, "Weather details", 11, TEXT, True
        ).pack(anchor="w")

        self.precipitation_label = self.label(
            precip_card,
            "Rainfall: --\nCloud cover: --\nSunrise: --\nSunset: --",
            9,
            MUTED
        )
        self.precipitation_label.pack(anchor="w", pady=(8, 0))

    # =====================================================
    # API REQUESTS
    # =====================================================

    def load_default_city(self):
        if API_KEY:
            self.search_weather()
        else:
            self.status.config(
                text="Add OPENWEATHER_API_KEY to your .env file.",
                fg="#B94A55"
            )

    def search_weather(self):
        city = self.search_entry.get().strip()

        if not city:
            self.status.config(text="Please enter a city name.", fg="#B94A55")
            return

        if not API_KEY:
            messagebox.showwarning(
                "API Key Required",
                "Create a .env file in this folder with:\n\n"
                "OPENWEATHER_API_KEY=your_actual_api_key"
            )
            return

        if self.busy:
            return

        self.busy = True
        self.request_number += 1
        request_id = self.request_number

        self.status.config(text=f"Loading weather for {city}...", fg=MUTED)

        threading.Thread(
            target=self.fetch_data,
            args=(city, request_id, self.unit),
            daemon=True
        ).start()

    def fetch_data(self, city, request_id, unit):
        try:
            params = {
                "q": city,
                "appid": API_KEY,
                "units": unit
            }

            current_response = requests.get(
                CURRENT_URL, params=params, timeout=12
            )

            if not current_response.ok:
                raise RuntimeError(self.api_error(current_response))

            forecast_response = requests.get(
                FORECAST_URL, params=params, timeout=12
            )

            if not forecast_response.ok:
                raise RuntimeError(self.api_error(forecast_response))

            current = current_response.json()
            forecast = forecast_response.json()

            self.root.after(
                0,
                lambda: self.show_weather(
                    request_id, city, current, forecast, unit
                )
            )

        except requests.exceptions.Timeout:
            self.show_error_later(
                request_id, "Request timed out. Please try again."
            )
        except requests.exceptions.RequestException:
            self.show_error_later(
                request_id, "Network error. Check your internet connection."
            )
        except RuntimeError as error:
            self.show_error_later(request_id, str(error))
        except (ValueError, KeyError, TypeError):
            self.show_error_later(
                request_id, "The weather service returned unexpected data."
            )

    def api_error(self, response):
        try:
            message = response.json().get("message", "")
        except ValueError:
            message = ""

        if response.status_code == 401:
            return "API key is invalid or not active yet."
        if response.status_code == 404:
            return "City not found. Try a city name such as Shimla or London."
        if response.status_code == 429:
            return "API request limit reached. Try again later."

        return message or f"Weather API error: {response.status_code}"

    def show_error_later(self, request_id, message):
        try:
            self.root.after(
                0, lambda: self.show_error(request_id, message)
            )
        except tk.TclError:
            pass

    def show_error(self, request_id, message):
        if request_id != self.request_number:
            return

        self.busy = False
        self.status.config(text=message, fg="#B94A55")

    # =====================================================
    # DISPLAY API DATA
    # =====================================================

    def show_weather(self, request_id, city, current, forecast, unit):
        if request_id != self.request_number:
            return

        if unit != self.unit:
            self.busy = False
            return

        try:
            self.current_data = current
            self.forecast_data = forecast
            self.city = city

            main = current["main"]
            weather = current["weather"][0]
            wind = current.get("wind", {})
            sys_data = current.get("sys", {})

            city_name = current.get("name", city)
            country = sys_data.get("country", "")
            description = weather.get("description", "Unknown").title()
            condition = weather.get("main", description)

            self.location_label.config(
                text=f"{city_name}, {country}  •  "
                     f"{datetime.now().strftime('%a, %d %b %I:%M %p')}"
            )
            self.weather_icon.config(text=icon_for(condition))
            self.temperature.config(
                text=temp_text(float(main["temp"]), unit)
            )
            self.condition.config(text=description)
            self.feels.config(
                text=f"Feels like {temp_text(float(main['feels_like']), unit)}"
            )

            self.metric_labels["humidity"].config(
                text=f"{main.get('humidity', '--')}%"
            )

            wind_speed = float(wind.get("speed", 0))
            wind_unit = "m/s" if unit == "metric" else "mph"
            self.metric_labels["wind"].config(
                text=f"{wind_speed:.1f} {wind_unit}"
            )

            self.metric_labels["pressure"].config(
                text=f"{main.get('pressure', '--')} hPa"
            )

            self.metric_labels["feels"].config(
                text=temp_text(float(main["feels_like"]), unit)
            )

            self.display_hourly(forecast, unit)
            self.display_weekly(forecast, unit)
            self.display_details(current, forecast)

            self.status.config(
                text=f"Weather updated for {city_name}.",
                fg=TEAL
            )
            self.chart.after(50, self.draw_chart)

        except (KeyError, IndexError, ValueError, TypeError):
            self.status.config(
                text="Weather data is incomplete. Try another city.",
                fg="#B94A55"
            )
        finally:
            self.busy = False

    # =====================================================
    # HOURLY FORECAST
    # =====================================================

    def display_hourly(self, forecast, unit):
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()

        entries = forecast.get("list", [])[:6]

        if not entries:
            self.label(
                self.hourly_frame, "No forecast data available.",
                9, MUTED
            ).pack(anchor="w")
            return

        for index, item in enumerate(entries):
            self.hourly_frame.grid_columnconfigure(index, weight=1)

            timestamp = datetime.fromtimestamp(item["dt"])
            weather = item["weather"][0]
            temp = float(item["main"]["temp"])

            cell = tk.Frame(
                self.hourly_frame,
                bg="#F4F7FA",
                padx=4,
                pady=8
            )
            cell.grid(
                row=0, column=index, sticky="nsew",
                padx=(0, 3) if index < len(entries) - 1 else (0, 0)
            )

            self.label(
                cell, timestamp.strftime("%H:%M"), 8,
                MUTED, False, "#F4F7FA", "center"
            ).pack(anchor="center")

            self.label(
                cell, icon_for(weather.get("main", "")), 15,
                TEAL, True, "#F4F7FA", "center"
            ).pack(anchor="center", pady=4)

            self.label(
                cell, temp_text(temp, unit), 9,
                TEXT, True, "#F4F7FA", "center"
            ).pack(anchor="center")

    # =====================================================
    # WEEKLY FORECAST
    # =====================================================

    def display_weekly(self, forecast, unit):
        for widget in self.weekly_frame.winfo_children():
            widget.destroy()

        grouped = defaultdict(list)

        for item in forecast.get("list", []):
            date = item.get("dt_txt", "")[:10]
            if date:
                grouped[date].append(item)

        dates = sorted(grouped.keys())[:5]

        if not dates:
            self.label(
                self.weekly_frame, "No weekly forecast available.",
                9, MUTED
            ).pack(anchor="w")
            return

        for index, date in enumerate(dates):
            entries = grouped[date]

            midday = min(
                entries,
                key=lambda item: abs(
                    int(item["dt_txt"][11:13]) - 12
                )
            )

            temps = [float(item["main"]["temp"]) for item in entries]
            weather = midday["weather"][0]
            condition = weather.get("main", "")

            try:
                date_label = datetime.strptime(
                    date, "%Y-%m-%d"
                ).strftime("%a, %d %b")
            except ValueError:
                date_label = date

            row = tk.Frame(
                self.weekly_frame,
                bg="#F4F7FA",
                padx=8,
                pady=6
            )
            row.pack(fill="x", pady=(0, 3))

            self.label(
                row, date_label, 8, TEXT, True, "#F4F7FA"
            ).pack(side="left")

            self.label(
                row, icon_for(condition), 13, TEXT,
                True, "#F4F7FA"
            ).pack(side="left", padx=10)

            self.label(
                row,
                f"{round(max(temps))}° / {round(min(temps))}°",
                9, TEAL, True, "#F4F7FA"
            ).pack(side="right")

    # =====================================================
    # ADDITIONAL DETAILS
    # =====================================================

    def display_details(self, current, forecast):
        rain = current.get("rain", {}).get("1h")
        clouds = current.get("clouds", {}).get("all", "--")
        sys_data = current.get("sys", {})

        sunrise = sys_data.get("sunrise")
        sunset = sys_data.get("sunset")

        def format_time(timestamp):
            if not timestamp:
                return "--"
            return datetime.fromtimestamp(timestamp).strftime("%I:%M %p")

        rain_text = f"{rain} mm in last hour" if rain is not None else "No recent rain reported"

        self.precipitation_label.config(
            text=(
                f"Rainfall: {rain_text}\n"
                f"Cloud cover: {clouds}%\n"
                f"Sunrise: {format_time(sunrise)}\n"
                f"Sunset: {format_time(sunset)}"
            )
        )

    # =====================================================
    # TEMPERATURE CHART
    # =====================================================

    def draw_chart(self, _event=None):
        canvas = self.chart
        canvas.delete("all")

        width = max(canvas.winfo_width(), 200)
        height = max(canvas.winfo_height(), 130)

        left, right = 32, width - 12
        top, bottom = 15, height - 25

        # Empty-state chart
        if not self.forecast_data:
            for i in range(4):
                y = top + i * (bottom - top) / 3
                canvas.create_line(
                    left, y, right, y,
                    fill="#E8EEF0"
                )

            canvas.create_text(
                width / 2,
                height / 2,
                text="Search a city to load temperature trend",
                fill=MUTED,
                font=("Segoe UI", 9)
            )
            return

        entries = self.forecast_data.get("list", [])[:10]
        if len(entries) < 2:
            return

        values = [float(item["main"]["temp"]) for item in entries]
        minimum = min(values) - 2
        maximum = max(values) + 2

        if maximum == minimum:
            maximum += 1

        # Grid lines
        for i in range(4):
            y = top + i * (bottom - top) / 3
            canvas.create_line(
                left, y, right, y,
                fill="#E7ECEF"
            )

        points = []
        x_step = (right - left) / (len(values) - 1)

        for i, value in enumerate(values):
            x = left + i * x_step
            y = bottom - (
                (value - minimum) / (maximum - minimum)
            ) * (bottom - top)

            points.extend([x, y])

        # Filled area
        polygon = [left, bottom] + points + [right, bottom]
        canvas.create_polygon(
            polygon,
            fill="#DDF0F0",
            outline=""
        )

        # Temperature curve
        canvas.create_line(
            *points,
            fill="#55A9B9",
            width=3,
            smooth=True
        )

        # Points and time labels
        for i, item in enumerate(entries):
            x = left + i * x_step
            y = points[i * 2 + 1]

            canvas.create_oval(
                x - 3, y - 3, x + 3, y + 3,
                fill=TEAL,
                outline=WHITE
            )

            if i % 2 == 0:
                time_text = item.get("dt_txt", "")[11:16]
                canvas.create_text(
                    x, bottom + 13,
                    text=time_text,
                    fill=MUTED,
                    font=("Segoe UI", 7)
                )

        canvas.create_text(
            5, top,
            text=f"{round(maximum)}°",
            anchor="w",
            fill=MUTED,
            font=("Segoe UI", 7)
        )

        canvas.create_text(
            5, bottom,
            text=f"{round(minimum)}°",
            anchor="w",
            fill=MUTED,
            font=("Segoe UI", 7)
        )

    # =====================================================
    # UNIT SWITCHING
    # =====================================================

    def toggle_unit(self):
        self.unit = "imperial" if self.unit == "metric" else "metric"

        self.unit_button.config(
            text="°F" if self.unit == "metric" else "°C"
        )

        if self.current_data:
            city = self.search_entry.get().strip()
            self.search_weather()
        else:
            self.status.config(
                text="Unit changed. Search a city to refresh weather."
            )


# =========================================================
# ENTRY POINT
# =========================================================

def main():
    root = tk.Tk()
    ClimaDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
