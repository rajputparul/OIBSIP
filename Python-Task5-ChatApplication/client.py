import socket
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog


HOST = "127.0.0.1"
PORT = 5555


class ChatClient:

    def __init__(self, root):
        self.root = root
        self.root.title("💬 Python Chat Application")
        self.root.geometry("900x650")
        self.root.minsize(750, 550)

        self.socket = None
        self.username = ""
        self.current_room = "General"
        self.connected = False

        self.build_login_screen()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )

    # ==========================================================
    # LOGIN SCREEN
    # ==========================================================

    def build_login_screen(self):
        self.clear_window()

        container = tk.Frame(
            self.root,
            padx=40,
            pady=40
        )
        container.pack(expand=True)

        tk.Label(
            container,
            text="💬 Python Chat Application",
            font=("Arial", 26, "bold")
        ).pack(pady=(0, 10))

        tk.Label(
            container,
            text="Real-time messaging with rooms",
            font=("Arial", 12)
        ).pack(pady=(0, 30))

        tk.Label(
            container,
            text="Username",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        self.username_entry = tk.Entry(
            container,
            width=35,
            font=("Arial", 12)
        )
        self.username_entry.pack(
            pady=(5, 15)
        )

        tk.Label(
            container,
            text="Password",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        self.password_entry = tk.Entry(
            container,
            width=35,
            font=("Arial", 12),
            show="*"
        )
        self.password_entry.pack(
            pady=(5, 20)
        )

        button_frame = tk.Frame(container)
        button_frame.pack()

        tk.Button(
            button_frame,
            text="Login",
            width=14,
            command=self.login
        ).grid(
            row=0,
            column=0,
            padx=5
        )

        tk.Button(
            button_frame,
            text="Register",
            width=14,
            command=self.register
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        self.login_status = tk.Label(
            container,
            text="",
            font=("Arial", 10)
        )
        self.login_status.pack(
            pady=20
        )

        self.password_entry.bind(
            "<Return>",
            lambda event: self.login()
        )

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.login_status.config(
                text="Please enter username and password."
            )
            return

        try:
            from database import register_user

            success, message = register_user(
                username,
                password
            )

            self.login_status.config(
                text=message
            )

            if success:
                self.password_entry.delete(
                    0,
                    tk.END
                )

        except Exception as error:
            self.login_status.config(
                text=f"Registration error: {error}"
            )

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.login_status.config(
                text="Please enter username and password."
            )
            return

        try:
            from database import verify_login

            if not verify_login(
                username,
                password
            ):
                self.login_status.config(
                    text="Invalid username or password."
                )
                return

        except Exception as error:
            self.login_status.config(
                text=f"Login error: {error}"
            )
            return

        self.username = username

        self.connect_to_server()

    # ==========================================================
    # CONNECT TO SERVER
    # ==========================================================

    def connect_to_server(self):
        try:
            self.socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            self.socket.connect(
                (HOST, PORT)
            )

            self.connected = True

            # Receive initial server request.
            first_data = self.socket.recv(
                1024
            )

            if not first_data:
                raise ConnectionError(
                    "Server closed the connection."
                )

            first_message = first_data.decode(
                "utf-8"
            )

            if "USERNAME_REQUIRED" in first_message:

                self.socket.sendall(
                    (
                        self.username + "\n"
                    ).encode("utf-8")
                )

            # IMPORTANT:
            # Build the GUI BEFORE starting the receiver
            # thread. This prevents ROOM_LIST messages from
            # arriving before the Listbox exists.

            self.build_chat_screen()

            # Start receiving messages after GUI exists.

            threading.Thread(
                target=self.receive_messages,
                daemon=True
            ).start()

            # Explicitly request the latest room list.

            self.send_command(
                "/rooms"
            )

        except ConnectionRefusedError:
            self.connected = False

            messagebox.showerror(
                "Connection Error",
                "Could not connect to the chat server.\n\n"
                "Please make sure server.py is running."
            )

        except Exception as error:
            self.connected = False

            messagebox.showerror(
                "Connection Error",
                str(error)
            )

    # ==========================================================
    # CHAT SCREEN
    # ==========================================================

    def build_chat_screen(self):
        self.clear_window()

        # ---------------- TOP BAR ----------------

        top_bar = tk.Frame(
            self.root,
            padx=10,
            pady=10
        )
        top_bar.pack(
            fill="x"
        )

        tk.Label(
            top_bar,
            text="💬 Python Chat",
            font=("Arial", 18, "bold")
        ).pack(
            side="left"
        )

        tk.Label(
            top_bar,
            text=f"Logged in as: {self.username}",
            font=("Arial", 10)
        ).pack(
            side="right",
            padx=10
        )

        # ---------------- MAIN AREA ----------------

        main_frame = tk.Frame(
            self.root
        )
        main_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        # ======================================================
        # ROOM PANEL
        # ======================================================

        room_frame = tk.Frame(
            main_frame,
            width=180
        )
        room_frame.pack(
            side="left",
            fill="y",
            padx=(0, 10)
        )

        tk.Label(
            room_frame,
            text="🏠 Chat Rooms",
            font=("Arial", 13, "bold")
        ).pack(
            pady=(0, 10)
        )

        self.room_listbox = tk.Listbox(
            room_frame,
            width=22,
            height=20,
            font=("Arial", 11)
        )
        self.room_listbox.pack(
            fill="both",
            expand=True
        )

        # Always show General initially.
        self.room_listbox.insert(
            tk.END,
            "General"
        )

        self.room_listbox.selection_set(0)

        self.room_listbox.bind(
            "<Double-Button-1>",
            self.join_selected_room
        )

        tk.Button(
            room_frame,
            text="➕ Create Room",
            command=self.create_room
        ).pack(
            fill="x",
            pady=(10, 5)
        )

        tk.Button(
            room_frame,
            text="🚪 Join Room",
            command=self.join_selected_room
        ).pack(
            fill="x"
        )

        # ======================================================
        # CHAT PANEL
        # ======================================================

        chat_frame = tk.Frame(
            main_frame
        )
        chat_frame.pack(
            side="right",
            fill="both",
            expand=True
        )

        # Room title

        room_title_frame = tk.Frame(
            chat_frame
        )
        room_title_frame.pack(
            fill="x",
            pady=(0, 8)
        )

        self.room_title = tk.Label(
            room_title_frame,
            text="General",
            font=("Arial", 16, "bold")
        )
        self.room_title.pack(
            side="left"
        )

        self.connection_status = tk.Label(
            room_title_frame,
            text="● Connected",
            font=("Arial", 10)
        )
        self.connection_status.pack(
            side="right"
        )

        # ======================================================
        # CHAT DISPLAY
        # ======================================================

        display_frame = tk.Frame(
            chat_frame
        )
        display_frame.pack(
            fill="both",
            expand=True
        )

        self.chat_text = tk.Text(
            display_frame,
            wrap="word",
            font=("Arial", 11),
            state="disabled"
        )
        self.chat_text.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = tk.Scrollbar(
            display_frame,
            command=self.chat_text.yview
        )
        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.chat_text.config(
            yscrollcommand=scrollbar.set
        )

        # ======================================================
        # MESSAGE INPUT
        # ======================================================

        input_frame = tk.Frame(
            chat_frame,
            pady=10
        )
        input_frame.pack(
            fill="x"
        )

        self.message_entry = tk.Entry(
            input_frame,
            font=("Arial", 12)
        )
        self.message_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        tk.Button(
            input_frame,
            text="Send",
            width=10,
            command=self.send_message
        ).pack(
            side="right"
        )

        self.message_entry.bind(
            "<Return>",
            lambda event: self.send_message()
        )

        # ======================================================
        # EMOJI BUTTONS
        # ======================================================

        bottom_frame = tk.Frame(
            chat_frame
        )
        bottom_frame.pack(
            fill="x"
        )

        emoji_buttons = [
            ("😊", ":smile:"),
            ("❤️", ":heart:"),
            ("😂", ":laugh:"),
            ("👍", ":thumbsup:")
        ]

        for emoji, shortcode in emoji_buttons:

            tk.Button(
                bottom_frame,
                text=emoji,
                width=4,
                command=lambda code=shortcode:
                self.insert_emoji(code)
            ).pack(
                side="left",
                padx=2
            )

        tk.Button(
            bottom_frame,
            text="Disconnect",
            command=self.disconnect
        ).pack(
            side="right"
        )

        self.message_entry.focus_set()

    # ==========================================================
    # RECEIVE SERVER DATA
    # ==========================================================

    def receive_messages(self):

        buffer = ""

        while self.connected:

            try:
                data = self.socket.recv(
                    4096
                )

                if not data:
                    break

                buffer += data.decode(
                    "utf-8"
                )

                # Process complete lines only.
                while "\n" in buffer:

                    message, buffer = buffer.split(
                        "\n",
                        1
                    )

                    message = message.strip()

                    if not message:
                        continue

                    # ------------------------------------------
                    # CONNECTION
                    # ------------------------------------------

                    if message.startswith(
                        "CONNECTED|"
                    ):

                        room = message.split(
                            "|",
                            1
                        )[1]

                        self.root.after(
                            0,
                            lambda r=room:
                            self.handle_connected_room(r)
                        )

                        continue

                    # ------------------------------------------
                    # ROOM LIST
                    # ------------------------------------------

                    if message.startswith(
                        "ROOM_LIST|"
                    ):

                        room_data = message.split(
                            "|",
                            1
                        )[1]

                        rooms = [
                            room
                            for room in room_data.split("|")
                            if room.strip()
                        ]

                        self.root.after(
                            0,
                            lambda r=rooms:
                            self.update_room_list(r)
                        )

                        continue

                    # ------------------------------------------
                    # ROOM CHANGED
                    # ------------------------------------------

                    if message.startswith(
                        "ROOM_CHANGED|"
                    ):

                        room = message.split(
                            "|",
                            1
                        )[1]

                        self.root.after(
                            0,
                            lambda r=room:
                            self.handle_room_changed(r)
                        )

                        continue

                    # ------------------------------------------
                    # NORMAL MESSAGE
                    # ------------------------------------------

                    self.root.after(
                        0,
                        lambda m=message:
                        self.display_message(m)
                    )

            except (
                ConnectionResetError,
                BrokenPipeError,
                OSError
            ):
                break

        if self.connected:

            self.root.after(
                0,
                self.server_disconnected
            )

    # ==========================================================
    # SEND COMMAND
    # ==========================================================

    def send_command(self, command):

        if not self.connected:
            return False

        try:
            self.socket.sendall(
                (
                    command + "\n"
                ).encode("utf-8")
            )

            return True

        except (
            BrokenPipeError,
            ConnectionResetError,
            OSError
        ):
            self.disconnect()
            return False

    # ==========================================================
    # SEND CHAT MESSAGE
    # ==========================================================

    def send_message(self):

        message = self.message_entry.get().strip()

        if not message:
            return

        if not self.connected:
            messagebox.showwarning(
                "Disconnected",
                "You are not connected to the server."
            )
            return

        message = self.convert_emoji(
            message
        )

        if self.send_command(message):

            self.message_entry.delete(
                0,
                tk.END
            )

    # ==========================================================
    # DISPLAY MESSAGE
    # ==========================================================

    def display_message(self, message):

        self.chat_text.config(
            state="normal"
        )

        self.chat_text.insert(
            tk.END,
            message + "\n"
        )

        self.chat_text.see(
            tk.END
        )

        self.chat_text.config(
            state="disabled"
        )

    # ==========================================================
    # CREATE ROOM
    # ==========================================================

    def create_room(self):

        if not self.connected:
            return

        room_name = simpledialog.askstring(
            "Create Room",
            "Enter room name:"
        )

        if not room_name:
            return

        room_name = room_name.strip()

        if not room_name:
            return

        self.send_command(
            f"/create {room_name}"
        )

    # ==========================================================
    # JOIN ROOM
    # ==========================================================

    def join_selected_room(
        self,
        event=None
    ):

        if not self.connected:
            return

        selection = self.room_listbox.curselection()

        if not selection:
            return

        room_name = self.room_listbox.get(
            selection[0]
        )

        if room_name == self.current_room:
            return

        self.send_command(
            f"/join {room_name}"
        )

    # ==========================================================
    # UPDATE ROOM LIST
    # ==========================================================

    def update_room_list(self, rooms):

        if not hasattr(
            self,
            "room_listbox"
        ):
            return

        # Remove duplicates while preserving order.
        unique_rooms = []

        for room in rooms:

            room = room.strip()

            if room and room not in unique_rooms:
                unique_rooms.append(room)

        # Make sure General always exists.
        if "General" not in unique_rooms:
            unique_rooms.insert(
                0,
                "General"
            )

        self.room_listbox.delete(
            0,
            tk.END
        )

        for room in unique_rooms:

            self.room_listbox.insert(
                tk.END,
                room
            )

        # Select current room.
        for index, room in enumerate(
            unique_rooms
        ):

            if room == self.current_room:

                self.room_listbox.selection_clear(
                    0,
                    tk.END
                )

                self.room_listbox.selection_set(
                    index
                )

                self.room_listbox.activate(
                    index
                )

                break

    # ==========================================================
    # CONNECTION ROOM
    # ==========================================================

    def handle_connected_room(
        self,
        room
    ):

        self.current_room = room

        self.room_title.config(
            text=room
        )

        self.select_room_in_list(
            room
        )

    # ==========================================================
    # ROOM CHANGED
    # ==========================================================

    def handle_room_changed(
        self,
        room
    ):

        self.current_room = room

        self.room_title.config(
            text=room
        )

        self.select_room_in_list(
            room
        )

        # Clear old room messages.
        self.chat_text.config(
            state="normal"
        )

        self.chat_text.delete(
            "1.0",
            tk.END
        )

        self.chat_text.config(
            state="disabled"
        )

    # ==========================================================
    # SELECT ROOM IN LIST
    # ==========================================================

    def select_room_in_list(
        self,
        room_name
    ):

        if not hasattr(
            self,
            "room_listbox"
        ):
            return

        items = self.room_listbox.get(
            0,
            tk.END
        )

        for index, room in enumerate(items):

            if room == room_name:

                self.room_listbox.selection_clear(
                    0,
                    tk.END
                )

                self.room_listbox.selection_set(
                    index
                )

                self.room_listbox.activate(
                    index
                )

                self.room_listbox.see(
                    index
                )

                break

    # ==========================================================
    # EMOJI
    # ==========================================================

    def insert_emoji(
        self,
        shortcode
    ):

        self.message_entry.insert(
            tk.END,
            shortcode + " "
        )

        self.message_entry.focus_set()

    @staticmethod
    def convert_emoji(message):

        replacements = {
            ":smile:": "😊",
            ":heart:": "❤️",
            ":laugh:": "😂",
            ":thumbsup:": "👍",
            ":sad:": "😢",
            ":angry:": "😠",
            ":fire:": "🔥",
            ":rocket:": "🚀",
            ":ok:": "👌"
        }

        for shortcode, emoji in replacements.items():

            message = message.replace(
                shortcode,
                emoji
            )

        return message

    # ==========================================================
    # DISCONNECT
    # ==========================================================

    def disconnect(self):

        if not self.connected:
            return

        self.connected = False

        try:

            self.socket.sendall(
                b"/quit\n"
            )

        except OSError:
            pass

        try:

            self.socket.close()

        except OSError:
            pass

        if hasattr(
            self,
            "connection_status"
        ):

            self.connection_status.config(
                text="● Disconnected"
            )

    # ==========================================================
    # SERVER DISCONNECTED
    # ==========================================================

    def server_disconnected(self):

        self.connected = False

        if hasattr(
            self,
            "connection_status"
        ):

            self.connection_status.config(
                text="● Server disconnected"
            )

        messagebox.showwarning(
            "Server Disconnected",
            "The chat server has disconnected."
        )

    # ==========================================================
    # CLOSE APPLICATION
    # ==========================================================

    def close_application(self):

        if self.connected:

            answer = messagebox.askyesno(
                "Exit Chat",
                "Are you sure you want to exit?"
            )

            if not answer:
                return

            self.disconnect()

        self.root.destroy()

    # ==========================================================
    # UTILITY
    # ==========================================================

    def clear_window(self):

        for widget in self.root.winfo_children():
            widget.destroy()


# ==============================================================
# START APPLICATION
# ==============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = ChatClient(root)

    root.mainloop()