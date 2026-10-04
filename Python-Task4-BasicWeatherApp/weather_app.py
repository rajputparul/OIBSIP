import os
import threading
from datetime import datetime
from io import BytesIO

import requests
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from dotenv import load_dotenv


# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
ICON_URL = "https://openweathermap.org/img/wn/{}@2x.png"


# ---------------------------------------------------------
# WEATHER APPLICATION
# ---------------------------------------------------------

class WeatherApp:

    def __init__(self, root):

        self.root = root

        self.root.title("Weather App")
        self.root.geometry("1100x760")
        self.root.minsize(900, 650)

        self.root.configure(bg="#eef5ff")

        # Default unit
        self.unit = "metric"

        # Last searched city
        self.last_city = ""

        # Keep image references alive
        self.icon_references = []

        self.create_styles()
        self.create_widgets()

    # -----------------------------------------------------
    # STYLES
    # -----------------------------------------------------

    def create_styles(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            background="#1e3a5f",
            foreground="white",
            font=("Segoe UI", 24, "bold")
        )

        style.configure(
            "Subtitle.TLabel",
            background="#1e3a5f",
            foreground="#dcecff",
            font=("Segoe UI", 11)
        )

        style.configure(
            "CardTitle.TLabel",
            background="white",
            foreground="#1e3a5f",
            font=("Segoe UI", 13, "bold")
        )

        style.configure(
            "WeatherValue.TLabel",
            background="white",
            foreground="#172b4d",
            font=("Segoe UI", 30, "bold")
        )

        style.configure(
            "WeatherInfo.TLabel",
            background="white",
            foreground="#455a73",
            font=("Segoe UI", 10)
        )

    # -----------------------------------------------------
    # CREATE GUI
    # -----------------------------------------------------

    def create_widgets(self):

        # ================= HEADER =================

        header = tk.Frame(
            self.root,
            bg="#1e3a5f",
            height=125
        )

        header.pack(fill="x")
        header.pack_propagate(False)

        ttk.Label(
            header,
            text="Weather App",
            style="Title.TLabel"
        ).pack(pady=(18, 2))

        ttk.Label(
            header,
            text="Real-time weather, hourly forecast & 5-day forecast",
            style="Subtitle.TLabel"
        ).pack()

        # ================= SEARCH AREA =================

        search_frame = tk.Frame(
            self.root,
            bg="#eef5ff"
        )

        search_frame.pack(
            fill="x",
            padx=30,
            pady=20
        )

        self.city_entry = ttk.Entry(
            search_frame,
            font=("Segoe UI", 13),
            width=40
        )

        self.city_entry.pack(
            side="left",
            padx=(0, 10),
            ipady=7
        )

        self.city_entry.insert(0, "London")

        self.get_button = ttk.Button(
            search_frame,
            text="Get Weather",
            command=self.get_weather
        )

        self.get_button.pack(
            side="left",
            padx=5
        )

        self.unit_button = ttk.Button(
            search_frame,
            text="Switch to °F",
            command=self.toggle_unit
        )

        self.unit_button.pack(
            side="left",
            padx=5
        )

        # Enter key support
        self.city_entry.bind(
            "<Return>",
            lambda event: self.get_weather()
        )

        # ================= STATUS =================

        self.status_label = tk.Label(
            self.root,
            text="Enter a city and click Get Weather",
            bg="#eef5ff",
            fg="#36506b",
            font=("Segoe UI", 10)
        )

        self.status_label.pack()

        # ================= CURRENT WEATHER CARD =================

        current_card = tk.Frame(
            self.root,
            bg="white",
            highlightthickness=1,
            highlightbackground="#d5e3f2"
        )

        current_card.pack(
            fill="x",
            padx=30,
            pady=10
        )

        self.location_label = ttk.Label(
            current_card,
            text="Weather Information",
            style="CardTitle.TLabel"
        )

        self.location_label.pack(
            pady=(15, 5)
        )

        self.current_content = tk.Frame(
            current_card,
            bg="white"
        )

        self.current_content.pack(
            fill="x",
            padx=20,
            pady=(5, 20)
        )

        # Weather icon

        self.icon_label = tk.Label(
            self.current_content,
            bg="white"
        )

        self.icon_label.pack(
            side="left",
            padx=30
        )

        # Information

        info_frame = tk.Frame(
            self.current_content,
            bg="white"
        )

        info_frame.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.temperature_label = ttk.Label(
            info_frame,
            text="--°",
            style="WeatherValue.TLabel"
        )

        self.temperature_label.pack(
            anchor="w"
        )

        self.condition_label = ttk.Label(
            info_frame,
            text="Condition: --",
            style="WeatherInfo.TLabel"
        )

        self.condition_label.pack(
            anchor="w",
            pady=2
        )

        self.feels_label = ttk.Label(
            info_frame,
            text="Feels like: --",
            style="WeatherInfo.TLabel"
        )

        self.feels_label.pack(
            anchor="w",
            pady=2
        )

        self.humidity_label = ttk.Label(
            info_frame,
            text="Humidity: --",
            style="WeatherInfo.TLabel"
        )

        self.humidity_label.pack(
            anchor="w",
            pady=2
        )

        self.wind_label = ttk.Label(
            info_frame,
            text="Wind: --",
            style="WeatherInfo.TLabel"
        )

        self.wind_label.pack(
            anchor="w",
            pady=2
        )

        self.pressure_label = ttk.Label(
            info_frame,
            text="Pressure: --",
            style="WeatherInfo.TLabel"
        )

        self.pressure_label.pack(
            anchor="w",
            pady=2
        )

        # ================= FORECAST AREA =================

        forecast_container = tk.Frame(
            self.root,
            bg="#eef5ff"
        )

        forecast_container.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=10
        )

        # ================= HOURLY =================

        hourly_card = tk.Frame(
            forecast_container,
            bg="white",
            highlightthickness=1,
            highlightbackground="#d5e3f2"
        )

        hourly_card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 8)
        )

        ttk.Label(
            hourly_card,
            text="Next 6 Hours",
            style="CardTitle.TLabel"
        ).pack(
            pady=12
        )

        self.hourly_frame = tk.Frame(
            hourly_card,
            bg="white"
        )

        self.hourly_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        # ================= DAILY =================

        daily_card = tk.Frame(
            forecast_container,
            bg="white",
            highlightthickness=1,
            highlightbackground="#d5e3f2"
        )

        daily_card.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(8, 0)
        )

        ttk.Label(
            daily_card,
            text="5-Day Forecast",
            style="CardTitle.TLabel"
        ).pack(
            pady=12
        )

        self.daily_frame = tk.Frame(
            daily_card,
            bg="white"
        )

        self.daily_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

    # -----------------------------------------------------
    # STATUS MESSAGE
    # -----------------------------------------------------

    def set_status(self, message, error=False):

        self.status_label.config(
            text=message,
            fg="#b42318" if error else "#36506b"
        )

    # -----------------------------------------------------
    # GET WEATHER BUTTON
    # -----------------------------------------------------

    def get_weather(self):

        city = self.city_entry.get().strip()

        # Validate empty input

        if not city:

            self.set_status(
                "Please enter a city name or ZIP code.",
                error=True
            )

            return

        # Validate API key

        if not API_KEY:

            self.set_status(
                "API key not found. Check your .env file.",
                error=True
            )

            return

        self.get_button.config(
            state="disabled"
        )

        self.set_status(
            "Fetching weather data..."
        )

        # Run API request in background

        thread = threading.Thread(
            target=self.fetch_weather,
            args=(city,),
            daemon=True
        )

        thread.start()

    # -----------------------------------------------------
    # API REQUEST
    # -----------------------------------------------------

    def fetch_weather(self, city):

        try:

            params = {
                "q": city,
                "appid": API_KEY,
                "units": self.unit
            }

            # Current weather

            current_response = requests.get(
                CURRENT_URL,
                params=params,
                timeout=10
            )

            # Forecast

            forecast_response = requests.get(
                FORECAST_URL,
                params=params,
                timeout=10
            )

            # -----------------------------
            # API KEY ERROR
            # -----------------------------

            if current_response.status_code == 401:

                raise Exception(
                    "Invalid API key. Please check your OpenWeather API key."
                )

            # -----------------------------
            # CITY NOT FOUND
            # -----------------------------

            if current_response.status_code == 404:

                raise Exception(
                    "City not found. Please check the city name."
                )

            # -----------------------------
            # OTHER CURRENT WEATHER ERROR
            # -----------------------------

            if current_response.status_code != 200:

                raise Exception(
                    f"Weather service returned error "
                    f"{current_response.status_code}."
                )

            # -----------------------------
            # FORECAST ERROR
            # -----------------------------

            if forecast_response.status_code != 200:

                raise Exception(
                    f"Forecast service returned error "
                    f"{forecast_response.status_code}."
                )

            # Parse JSON

            current_data = current_response.json()
            forecast_data = forecast_response.json()

            # Send result back to Tkinter main thread

            self.root.after(
                0,
                lambda data=current_data, forecast=forecast_data:
                self.display_weather(data, forecast)
            )

        # -------------------------------------------------
        # TIMEOUT
        # -------------------------------------------------

        except requests.exceptions.Timeout:

            self.root.after(
                0,
                lambda:
                self.show_error(
                    "Network timeout. Please check your internet connection."
                )
            )

        # -------------------------------------------------
        # CONNECTION ERROR
        # -------------------------------------------------

        except requests.exceptions.ConnectionError:

            self.root.after(
                0,
                lambda:
                self.show_error(
                    "Network connection error. Please check your internet connection."
                )
            )

        # -------------------------------------------------
        # REQUEST ERROR
        # -------------------------------------------------

        except requests.exceptions.RequestException:

            self.root.after(
                0,
                lambda:
                self.show_error(
                    "Could not connect to the weather service."
                )
            )

        # -------------------------------------------------
        # OTHER ERROR
        # -------------------------------------------------

        except Exception as error:

            # IMPORTANT:
            # Capture error BEFORE lambda.
            # This prevents the Tkinter closure error.

            error_message = str(error)

            self.root.after(
                0,
                lambda message=error_message:
                self.show_error(message)
            )

    # -----------------------------------------------------
    # DISPLAY WEATHER
    # -----------------------------------------------------

    def display_weather(
        self,
        current,
        forecast
    ):

        try:

            city_name = current.get(
                "name",
                "Unknown"
            )

            country = current.get(
                "sys",
                {}
            ).get(
                "country",
                ""
            )

            self.last_city = city_name

            self.location_label.config(
                text=f"{city_name}, {country}"
            )

            # -----------------------------
            # WEATHER VALUES
            # -----------------------------

            temperature = current["main"]["temp"]

            feels_like = current["main"]["feels_like"]

            humidity = current["main"]["humidity"]

            pressure = current["main"]["pressure"]

            wind_speed = current["wind"]["speed"]

            description = current["weather"][0]["description"].title()

            icon_code = current["weather"][0]["icon"]

            # -----------------------------
            # UNIT
            # -----------------------------

            if self.unit == "metric":

                unit_symbol = "°C"
                wind_unit = "m/s"

            else:

                unit_symbol = "°F"
                wind_unit = "mph"

            # -----------------------------
            # UPDATE GUI
            # -----------------------------

            self.temperature_label.config(
                text=f"{temperature:.1f}{unit_symbol}"
            )

            self.condition_label.config(
                text=f"Condition: {description}"
            )

            self.feels_label.config(
                text=f"Feels like: {feels_like:.1f}{unit_symbol}"
            )

            self.humidity_label.config(
                text=f"Humidity: {humidity}%"
            )

            self.wind_label.config(
                text=f"Wind: {wind_speed:.1f} {wind_unit}"
            )

            self.pressure_label.config(
                text=f"Pressure: {pressure} hPa"
            )

            # -----------------------------
            # WEATHER ICON
            # -----------------------------

            self.load_icon(
                icon_code,
                self.icon_label
            )

            # -----------------------------
            # FORECASTS
            # -----------------------------

            self.display_hourly(
                forecast
            )

            self.display_daily(
                forecast
            )

            self.set_status(
                f"Weather updated for {city_name}."
            )

        except Exception as error:

            self.show_error(
                f"Could not display weather data: {error}"
            )

        finally:

            self.get_button.config(
                state="normal"
            )

    # -----------------------------------------------------
    # LOAD WEATHER ICON
    # -----------------------------------------------------

    def load_icon(
        self,
        icon_code,
        target_label
    ):

        try:

            response = requests.get(
                ICON_URL.format(icon_code),
                timeout=5
            )

            response.raise_for_status()

            image = Image.open(
                BytesIO(response.content)
            ).convert("RGBA")

            image = image.resize(
                (90, 90),
                Image.Resampling.LANCZOS
            )

            photo = ImageTk.PhotoImage(
                image
            )

            target_label.config(
                image=photo,
                text=""
            )

            # Keep reference alive

            self.icon_references.append(
                photo
            )

        except Exception:

            target_label.config(
                image="",
                text="☁",
                font=("Segoe UI", 40)
            )

    # -----------------------------------------------------
    # HOURLY FORECAST
    # -----------------------------------------------------

    def display_hourly(
        self,
        forecast
    ):

        # Clear old widgets

        for widget in self.hourly_frame.winfo_children():

            widget.destroy()

        # Get first 2 forecast entries
        # OpenWeather free forecast provides
        # 3-hour intervals.

        entries = forecast.get(
            "list",
            []
        )[:2]

        for entry in entries:

            self.create_forecast_card(
                self.hourly_frame,
                entry,
                hourly=True
            )

    # -----------------------------------------------------
    # DAILY FORECAST
    # -----------------------------------------------------

    def display_daily(
        self,
        forecast
    ):

        # Clear old widgets

        for widget in self.daily_frame.winfo_children():

            widget.destroy()

        daily_data = {}

        # Group forecast entries by date

        for entry in forecast.get(
            "list",
            []
        ):

            date_text = entry[
                "dt_txt"
            ].split(" ")[0]

            if date_text not in daily_data:

                daily_data[date_text] = []

            daily_data[
                date_text
            ].append(entry)

        # Take next 5 days

        dates = list(
            daily_data.keys()
        )[:5]

        for date_text in dates:

            entries = daily_data[
                date_text
            ]

            # Choose forecast closest to noon

            selected = min(
                entries,
                key=lambda item:
                abs(
                    int(
                        item["dt_txt"][11:13]
                    ) - 12
                )
            )

            self.create_forecast_card(
                self.daily_frame,
                selected,
                hourly=False
            )

    # -----------------------------------------------------
    # FORECAST CARD
    # -----------------------------------------------------

    def create_forecast_card(
        self,
        parent,
        entry,
        hourly=False
    ):

        card = tk.Frame(
            parent,
            bg="#f8fbff",
            highlightthickness=1,
            highlightbackground="#dce8f5"
        )

        card.pack(
            fill="x",
            pady=4
        )

        # Date/time

        date_time = datetime.strptime(
            entry["dt_txt"],
            "%Y-%m-%d %H:%M:%S"
        )

        if hourly:

            title = date_time.strftime(
                "%I:%M %p"
            )

        else:

            title = date_time.strftime(
                "%a, %d %b"
            )

        # Weather details

        description = entry[
            "weather"
        ][0][
            "description"
        ].title()

        icon_code = entry[
            "weather"
        ][0][
            "icon"
        ]

        temperature = entry[
            "main"
        ][
            "temp"
        ]

        if self.unit == "metric":

            unit_symbol = "°C"

        else:

            unit_symbol = "°F"

        # Text frame

        text_frame = tk.Frame(
            card,
            bg="#f8fbff"
        )

        text_frame.pack(
            side="left",
            fill="x",
            expand=True,
            padx=10,
            pady=6
        )

        tk.Label(
            text_frame,
            text=title,
            bg="#f8fbff",
            fg="#1e3a5f",
            font=("Segoe UI", 10, "bold")
        ).pack(
            anchor="w"
        )

        tk.Label(
            text_frame,
            text=description,
            bg="#f8fbff",
            fg="#607d98",
            font=("Segoe UI", 9)
        ).pack(
            anchor="w"
        )

        tk.Label(
            text_frame,
            text=f"{temperature:.1f}{unit_symbol}",
            bg="#f8fbff",
            fg="#172b4d",
            font=("Segoe UI", 13, "bold")
        ).pack(
            anchor="w"
        )

        # Icon

        icon_label = tk.Label(
            card,
            bg="#f8fbff"
        )

        icon_label.pack(
            side="right",
            padx=10
        )

        self.load_icon(
            icon_code,
            icon_label
        )

    # -----------------------------------------------------
    # °C / °F TOGGLE
    # -----------------------------------------------------

    def toggle_unit(self):

        if self.unit == "metric":

            self.unit = "imperial"

            self.unit_button.config(
                text="Switch to °C"
            )

        else:

            self.unit = "metric"

            self.unit_button.config(
                text="Switch to °F"
            )

        # Refresh current city

        if self.last_city:

            self.get_weather()

    # -----------------------------------------------------
    # ERROR DISPLAY
    # -----------------------------------------------------

    def show_error(
        self,
        message
    ):

        self.set_status(
            message,
            error=True
        )

        self.get_button.config(
            state="normal"
        )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    root = tk.Tk()

    WeatherApp(root)

    root.mainloop()


if __name__ == "__main__":

    main()