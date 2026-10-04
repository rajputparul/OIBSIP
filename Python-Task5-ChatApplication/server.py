import socket
import threading
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5555

clients = {}
rooms = {
    "General": set()
}

lock = threading.Lock()


def timestamp():
    return datetime.now().strftime("%H:%M")


def send_message(client_socket, message):
    try:
        client_socket.sendall(
            (message + "\n").encode("utf-8")
        )
    except (ConnectionResetError, BrokenPipeError, OSError):
        remove_client(client_socket)


def broadcast(room_name, message, exclude=None):
    with lock:
        room_clients = list(
            rooms.get(room_name, set())
        )

    for client_socket in room_clients:
        if client_socket != exclude:
            send_message(
                client_socket,
                message
            )


def broadcast_room_list():
    """Send the latest room list to every connected client."""

    with lock:
        room_names = sorted(rooms.keys())
        connected_clients = list(clients.keys())

    room_message = "ROOM_LIST|" + "|".join(
        room_names
    )

    for client_socket in connected_clients:
        send_message(
            client_socket,
            room_message
        )


def remove_client(client_socket):
    username = None
    room_name = None

    with lock:

        username = clients.pop(
            client_socket,
            None
        )

        for name, room_clients in rooms.items():

            if client_socket in room_clients:

                room_clients.remove(
                    client_socket
                )

                room_name = name
                break

    try:
        client_socket.close()
    except OSError:
        pass

    if username and room_name:

        broadcast(
            room_name,
            f"[{timestamp()}] System: "
            f"{username} disconnected."
        )

        broadcast_room_list()


def send_history(client_socket, room_name):
    """Send stored messages from SQLite."""

    try:
        from database import get_message_history

        history = get_message_history(
            room_name
        )

        for row in history:

            message = (
                f"[{row['timestamp']}] "
                f"{row['username']}: "
                f"{row['message']}"
            )

            send_message(
                client_socket,
                message
            )

    except Exception as error:
        print(
            f"[HISTORY ERROR] {error}"
        )


def save_chat_message(
    username,
    room_name,
    message
):
    """Save message centrally in SQLite."""

    try:
        from database import save_message

        save_message(
            username,
            room_name,
            message
        )

    except Exception as error:
        print(
            f"[DATABASE ERROR] {error}"
        )


def handle_client(
    client_socket,
    address
):

    username = None
    current_room = "General"

    try:

        # Ask for username
        send_message(
            client_socket,
            "USERNAME_REQUIRED"
        )

        data = client_socket.recv(
            1024
        )

        if not data:
            return

        username = data.decode(
            "utf-8"
        ).strip()

        if not username:
            username = f"User-{address[1]}"

        with lock:

            clients[
                client_socket
            ] = username

            rooms.setdefault(
                "General",
                set()
            ).add(
                client_socket
            )

        # Tell client connection succeeded
        send_message(
            client_socket,
            "CONNECTED|General"
        )

        # Send available rooms
        broadcast_room_list()

        # Send previous General history
        send_history(
            client_socket,
            "General"
        )

        # Notify other users
        broadcast(
            "General",
            f"[{timestamp()}] System: "
            f"{username} joined the room.",
            exclude=client_socket
        )

        print(
            f"[CONNECTED] "
            f"{username} - {address}"
        )

        buffer = ""

        while True:

            data = client_socket.recv(
                4096
            )

            if not data:
                break

            buffer += data.decode(
                "utf-8"
            )

            while "\n" in buffer:

                raw_message, buffer = buffer.split(
                    "\n",
                    1
                )

                message = raw_message.strip()

                if not message:
                    continue

                # ------------------------------------------
                # QUIT
                # ------------------------------------------

                if message == "/quit":
                    return

                # ------------------------------------------
                # CREATE ROOM
                # ------------------------------------------

                if message.startswith(
                    "/create "
                ):

                    new_room = message[
                        8:
                    ].strip()

                    if not new_room:

                        send_message(
                            client_socket,
                            "[System] Room name "
                            "cannot be empty."
                        )

                        continue

                    with lock:

                        if new_room not in rooms:

                            rooms[
                                new_room
                            ] = set()

                            room_created = True

                        else:

                            room_created = False

                    if room_created:

                        send_message(
                            client_socket,
                            f"[System] Room "
                            f"'{new_room}' created."
                        )

                        print(
                            f"[ROOM CREATED] "
                            f"{new_room} by "
                            f"{username}"
                        )

                    else:

                        send_message(
                            client_socket,
                            f"[System] Room "
                            f"'{new_room}' already exists."
                        )

                    # IMPORTANT:
                    # Send updated rooms to EVERYONE
                    broadcast_room_list()

                    continue

                # ------------------------------------------
                # ROOM LIST
                # ------------------------------------------

                if message == "/rooms":

                    broadcast_room_list()

                    continue

                # ------------------------------------------
                # JOIN ROOM
                # ------------------------------------------

                if message.startswith(
                    "/join "
                ):

                    new_room = message[
                        6:
                    ].strip()

                    with lock:

                        if new_room not in rooms:

                            room_exists = False

                        else:

                            room_exists = True

                            old_room = current_room

                            if client_socket in rooms.get(
                                old_room,
                                set()
                            ):

                                rooms[
                                    old_room
                                ].remove(
                                    client_socket
                                )

                            rooms[
                                new_room
                            ].add(
                                client_socket
                            )

                            current_room = new_room

                    if not room_exists:

                        send_message(
                            client_socket,
                            "[System] Room does not exist."
                        )

                        continue

                    # Tell client its room changed
                    send_message(
                        client_socket,
                        f"ROOM_CHANGED|{new_room}"
                    )

                    # Send room history
                    send_history(
                        client_socket,
                        new_room
                    )

                    # Notify old room
                    broadcast(
                        old_room,
                        f"[{timestamp()}] System: "
                        f"{username} left the room.",
                        exclude=client_socket
                    )

                    # Notify new room
                    broadcast(
                        new_room,
                        f"[{timestamp()}] System: "
                        f"{username} joined the room.",
                        exclude=client_socket
                    )

                    broadcast_room_list()

                    continue

                # ------------------------------------------
                # NORMAL CHAT MESSAGE
                # ------------------------------------------

                formatted_message = (
                    f"[{timestamp()}] "
                    f"{username}: "
                    f"{message}"
                )

                print(
                    f"[{current_room}] "
                    f"{username}: "
                    f"{message}"
                )

                # Save centrally
                save_chat_message(
                    username,
                    current_room,
                    message
                )

                # Send to everyone in room
                broadcast(
                    current_room,
                    formatted_message
                )

    except ConnectionResetError:
        pass

    except OSError:
        pass

    finally:

        remove_client(
            client_socket
        )

        print(
            f"[DISCONNECTED] "
            f"{username if username else address}"
        )


def start_server():

    try:
        from database import initialize_database

        initialize_database()

    except Exception as error:
        print(
            f"[DATABASE INIT ERROR] {error}"
        )

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server.bind(
        (HOST, PORT)
    )

    server.listen()

    print("=" * 55)
    print("        PYTHON REAL-TIME CHAT SERVER")
    print("=" * 55)
    print(
        f"Server running on "
        f"{HOST}:{PORT}"
    )
    print(
        "Waiting for clients..."
    )
    print(
        "Press CTRL+C to stop the server."
    )
    print("=" * 55)

    try:

        while True:

            client_socket, address = server.accept()

            client_thread = threading.Thread(
                target=handle_client,
                args=(
                    client_socket,
                    address
                ),
                daemon=True
            )

            client_thread.start()

            print(
                f"[NEW CONNECTION] "
                f"{address[0]}:"
                f"{address[1]}"
            )

    except KeyboardInterrupt:

        print(
            "\nServer shutting down..."
        )

    finally:

        with lock:
            connected_clients = list(
                clients.keys()
            )

        for client_socket in connected_clients:

            try:
                client_socket.close()

            except OSError:
                pass

        server.close()

        print(
            "Server stopped."
        )


if __name__ == "__main__":
    start_server()