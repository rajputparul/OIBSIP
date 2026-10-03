import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import wikipedia
import requests
import os
import threading
import time

from dotenv import load_dotenv


# ---------------- ENVIRONMENT ----------------
load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


# ---------------- TEXT TO SPEECH ----------------
engine = pyttsx3.init()

engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)


def speak(text):
    print("Assistant:", text)
    engine.say(text)
    engine.runAndWait()


# ---------------- VOICE INPUT ----------------
recognizer = sr.Recognizer()


def listen():
    with sr.Microphone() as source:
        print("\nListening...")

        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.5
        )

        try:
            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )

            command = recognizer.recognize_google(audio)
            command = command.lower()

            print("You:", command)

            return command

        except sr.WaitTimeoutError:
            print("No speech detected.")
            return ""

        except sr.UnknownValueError:
            speak("Sorry, I could not understand you.")
            return ""

        except sr.RequestError:
            speak("Speech recognition service is unavailable.")
            return ""


# ---------------- WEATHER ----------------
def get_weather(city):

    if not WEATHER_API_KEY:
        speak("Weather API key is not configured.")
        return

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        data = response.json()

        if response.status_code == 200:

            temperature = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]

            speak(
                f"The weather in {city} is {description}. "
                f"The temperature is {temperature:.1f} degrees Celsius. "
                f"It feels like {feels_like:.1f} degrees. "
                f"Humidity is {humidity} percent."
            )

        elif response.status_code == 404:

            speak(
                f"I could not find weather information for {city}."
            )

        elif response.status_code == 401:

            speak(
                "The weather API key is invalid or not activated."
            )

        else:

            speak(
                "Sorry, I could not get the weather information."
            )

    except requests.exceptions.RequestException:

        speak(
            "I am unable to connect to the weather service right now."
        )

    except Exception:

        speak(
            "Sorry, something went wrong while getting the weather."
        )


# ---------------- REMINDER ----------------
def set_reminder(seconds, message):

    def reminder_task():

        time.sleep(seconds)

        speak(
            f"Reminder! {message}"
        )

    reminder_thread = threading.Thread(
        target=reminder_task,
        daemon=True
    )

    reminder_thread.start()


def handle_reminder(command):

    try:

        words = command.split()

        seconds = None

        # Example:
        # remind me in 10 seconds
        if "seconds" in words:

            index = words.index("seconds")

            if index > 0:
                seconds = int(words[index - 1])

        # Example:
        # remind me in 5 minutes
        elif "minutes" in words:

            index = words.index("minutes")

            if index > 0:
                minutes = int(words[index - 1])
                seconds = minutes * 60

        # Example:
        # remind me in 1 minute
        elif "minute" in words:

            index = words.index("minute")

            if index > 0:
                minutes = int(words[index - 1])
                seconds = minutes * 60

        if seconds is None:

            speak(
                "Please tell me the reminder time, "
                "for example, remind me in 10 seconds."
            )

            return

        # Get reminder message
        if "to" in words:

            message = command.split("to", 1)[1].strip()

        else:

            message = "your reminder"

        set_reminder(
            seconds,
            message
        )

        if seconds < 60:

            speak(
                f"Okay, I will remind you in {seconds} seconds."
            )

        else:

            minutes = seconds // 60

            speak(
                f"Okay, I will remind you in {minutes} minutes."
            )

    except (ValueError, IndexError):

        speak(
            "Sorry, I could not understand the reminder."
        )


# ---------------- COMMAND HANDLER ----------------
def handle_command(command):

    if not command:
        return True

    # ---------------- EXIT ----------------
    if any(
        phrase in command
        for phrase in [
            "exit",
            "quit",
            "stop",
            "goodbye",
            "bye",
            "ok bye",
            "bye bye",
            "band ho jao",
            "band karo",
            "close yourself",
            "shut down"
        ]
    ):

        speak(
            "Goodbye! Have a nice day."
        )

        return False

    # ---------------- GREETING ----------------
    elif (
        "hello" in command
        or "hi" in command
        or "hey" in command
    ):

        speak(
            "Hello! How can I help you?"
        )

    # ---------------- REMINDER ----------------
    elif (
        "remind me" in command
        or "set a reminder" in command
        or "reminder" in command
    ):

        handle_reminder(command)

    # ---------------- TIME ----------------
    elif "time" in command:

        current_time = datetime.datetime.now().strftime(
            "%I:%M %p"
        )

        speak(
            f"The current time is {current_time}"
        )

    # ---------------- DATE ----------------
    elif "date" in command:

        current_date = datetime.datetime.now().strftime(
            "%d %B %Y"
        )

        speak(
            f"Today's date is {current_date}"
        )

    # ---------------- WEATHER ----------------
    elif "weather" in command:

        city = command.replace(
            "weather",
            ""
        ).strip()

        if city.startswith("in "):

            city = city[3:].strip()

        if city:

            speak(
                f"Checking the weather in {city}."
            )

            get_weather(city)

        else:

            speak(
                "Please tell me the city name."
            )

    # ---------------- OPEN GOOGLE ----------------
    elif "open google" in command:

        speak(
            "Opening Google."
        )

        webbrowser.open(
            "https://www.google.com"
        )

    # ---------------- OPEN YOUTUBE ----------------
    elif "open youtube" in command:

        speak(
            "Opening YouTube."
        )

        webbrowser.open(
            "https://www.youtube.com"
        )

    # ---------------- WEB SEARCH ----------------
    elif "search" in command:

        query = command.replace(
            "search",
            ""
        ).strip()

        if query:

            speak(
                f"Searching for {query}"
            )

            webbrowser.open(
                "https://www.google.com/search?q="
                + query.replace(" ", "+")
            )

        else:

            speak(
                "What should I search for?"
            )

    # ---------------- WIKIPEDIA ----------------
    elif "wikipedia" in command:

        topic = command.replace(
            "wikipedia",
            ""
        ).strip()

        if topic:

            try:

                speak(
                    f"Searching Wikipedia for {topic}"
                )

                result = wikipedia.summary(
                    topic,
                    sentences=2
                )

                speak(result)

            except wikipedia.exceptions.DisambiguationError:

                speak(
                    "There are multiple results for that topic."
                )

            except wikipedia.exceptions.PageError:

                speak(
                    "I could not find that topic on Wikipedia."
                )

            except Exception:

                speak(
                    "Sorry, I could not search Wikipedia."
                )

        else:

            speak(
                "Please tell me what you want to search on Wikipedia."
            )

    # ---------------- DEFAULT ----------------
    else:

        speak(
            "I heard you, but I do not have a command for that yet."
        )

    return True


# ---------------- MAIN PROGRAM ----------------
def main():

    speak(
        "Hello! I am your voice assistant."
    )

    speak(
        "You can ask me the time, date, weather, "
        "set reminders, open websites, search the web, "
        "or search Wikipedia."
    )

    running = True

    while running:

        command = listen()

        running = handle_command(command)


# ---------------- START PROGRAM ----------------
if __name__ == "__main__":
    main()