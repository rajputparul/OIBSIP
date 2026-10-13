import os
import re
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from flask_socketio import SocketIO, emit, join_room, rooms as socket_rooms

from database import (
    initialize_database,
    register_user,
    verify_login,
    get_recent_messages,
    save_message,
    get_room_names,
    create_room,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "CHAT_SECRET_KEY",
    "local-development-key-change-before-deployment"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

socketio = SocketIO(app, async_mode="threading")
initialize_database()

ROOM_PATTERN = re.compile(r"^[A-Za-z0-9 _-]{1,30}$")
MAX_MESSAGE_LENGTH = 2000


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def emit_room_list():
    socketio.emit("room_list", get_room_names())


@app.route("/")
def index():
    return redirect(url_for("chat" if "username" in session else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        success, message = register_user(
            request.form.get("username", ""),
            request.form.get("password", "")
        )
        flash(message, "success" if success else "error")
        if success:
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if verify_login(username, password):
            session.clear()
            session["username"] = username
            return redirect(url_for("chat"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/chat")
@login_required
def chat():
    return render_template(
        "chat.html",
        username=session["username"],
        rooms=get_room_names()
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@socketio.on("connect")
def on_connect(auth=None):
    if "username" not in session:
        return False


@socketio.on("join_room")
def on_join_room(data):
    if "username" not in session:
        return

    data = data or {}
    room = str(data.get("room", "General")).strip()

    if not ROOM_PATTERN.fullmatch(room):
        emit("chat_error", {"message": "Invalid room name."})
        return

    existing_rooms = get_room_names()
    actual_room = next(
        (name for name in existing_rooms if name.casefold() == room.casefold()),
        None
    )

    if actual_room is None:
        emit("chat_error", {"message": "Room does not exist. Create it first."})
        emit("room_list", existing_rooms)
        return

    # Leave previous chat rooms, but keep the private Socket.IO room.
    for joined in socket_rooms():
        if joined != request.sid:
            from flask_socketio import leave_room
            leave_room(joined)

    join_room(actual_room)

    emit("room_history", {
        "room": actual_room,
        "messages": get_recent_messages(actual_room)
    })


@socketio.on("create_room")
def on_create_room(data):
    if "username" not in session:
        return

    data = data or {}
    room = str(data.get("room", "")).strip()

    if not ROOM_PATTERN.fullmatch(room):
        emit("room_created", {
            "success": False,
            "message": "Use 1–30 letters, numbers, spaces, underscores or hyphens."
        })
        return

    success, result = create_room(room)

    if not success:
        emit("room_created", {
            "success": False,
            "message": result
        })
        return

    emit_room_list()
    emit("room_created", {
        "success": True,
        "room": result,
        "rooms": get_room_names()
    })


@socketio.on("send_message")
def on_send_message(data):
    if "username" not in session:
        return

    data = data or {}
    room = str(data.get("room", "General")).strip()
    message = str(data.get("message", "")).strip()

    if not ROOM_PATTERN.fullmatch(room):
        emit("chat_error", {"message": "Invalid room name."})
        return

    joined_rooms = socket_rooms()
    if room not in joined_rooms:
        emit("chat_error", {"message": "Join this room before sending a message."})
        return

    if not message or len(message) > MAX_MESSAGE_LENGTH:
        emit("chat_error", {
            "message": "Messages must be 1–2000 characters."
        })
        return

    saved = save_message(session["username"], room, message)
    socketio.emit("new_message", saved, to=room)


@socketio.on("typing")
def on_typing(data):
    if "username" not in session:
        return

    data = data or {}
    room = str(data.get("room", "")).strip()

    if not ROOM_PATTERN.fullmatch(room):
        return

    if room not in socket_rooms():
        return

    socketio.emit(
        "typing_status",
        {
            "username": session["username"],
            "room": room,
            "typing": bool(data.get("typing", False))
        },
        to=room,
        include_self=False
    )


if __name__ == "__main__":
    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )
