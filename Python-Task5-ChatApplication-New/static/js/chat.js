const socket = io();

const messagesArea = document.getElementById("messages");
const messageForm = document.getElementById("message-form");
const messageInput = document.getElementById("message-input");
const roomTitle = document.getElementById("current-room-title");
const roomList = document.getElementById("room-list");
const connectionPill = document.querySelector(".connection-pill");
const typingStatus = document.getElementById("typing-status");
const emptyState = document.getElementById("empty-state");
const welcomeBanner = document.querySelector(".welcome-banner");
const toast = document.getElementById("toast");
const emojiPicker = document.getElementById("emoji-picker");
const emojiButton = document.getElementById("emoji-btn");
const createRoomButton = document.getElementById("create-room-btn");

const currentUser =
    document.querySelector(".profile-info strong")?.textContent.trim() || "You";

let currentRoom = "General";
let typingTimer;
let toastTimer;
let typingHideTimer;
let messageCount = 0;

function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 2800);
}

function setConnectionStatus(connected) {
    if (!connectionPill) return;
    connectionPill.classList.toggle("offline", !connected);

    let dot = connectionPill.querySelector(".online-dot");
    if (!dot) {
        dot = document.createElement("span");
        dot.className = "online-dot";
        connectionPill.prepend(dot);
    }

    let label = connectionPill.querySelector(".connection-label");
    if (!label) {
        label = document.createElement("span");
        label.className = "connection-label";
        connectionPill.appendChild(label);
    }

    label.textContent = connected ? "Connected" : "Reconnecting...";
}

function updateEmptyState() {
    if (emptyState) emptyState.hidden = messageCount > 0;
    if (welcomeBanner) welcomeBanner.hidden = messageCount > 0;
}

function formatTime(value) {
    if (!value) return "";
    const date = new Date(value.replace(" ", "T") + "Z");
    if (Number.isNaN(date.getTime())) return "";
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function addMessage(message) {
    if (!messagesArea || !message || message.room !== currentRoom) return;

    if (welcomeBanner) welcomeBanner.hidden = true;
    if (emptyState) emptyState.hidden = true;

    const row = document.createElement("div");
    row.className = "message-row";

    const own = message.username === currentUser;
    if (own) row.classList.add("own-message");

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = String(message.username || "?").slice(0, 2).toUpperCase();

    const content = document.createElement("div");
    content.className = "message-content";

    const meta = document.createElement("div");
    meta.className = "message-meta";

    const name = document.createElement("strong");
    name.textContent = own ? "You" : (message.username || "User");

    const time = document.createElement("span");
    time.textContent = formatTime(message.created_at);

    meta.append(name, time);

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = message.message || "";

    content.append(meta, bubble);
    row.append(avatar, content);
    messagesArea.appendChild(row);

    messageCount++;
    updateEmptyState();
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function clearMessages() {
    if (messagesArea) {
        messagesArea.querySelectorAll(".message-row, .date-divider").forEach(
            element => element.remove()
        );
    }

    messageCount = 0;
    updateEmptyState();

    if (typingStatus) typingStatus.textContent = "";
}

function setActiveRoom(room) {
    currentRoom = room;
    if (roomTitle) roomTitle.textContent = room;

    document.querySelectorAll(".room-item").forEach(button => {
        button.classList.toggle("selected", button.dataset.room === room);
        button.classList.toggle("active", button.dataset.room === room);
    });

    const inputPlaceholder = messageInput;
    if (inputPlaceholder) inputPlaceholder.placeholder = `Message #${room}...`;
}

function joinRoom(room) {
    if (!room || room === currentRoom) return;
    clearMessages();
    setActiveRoom(room);
    socket.emit("join_room", { room });
}

function renderRoomList(rooms) {
    if (!roomList || !Array.isArray(rooms)) return;

    roomList.replaceChildren();

    rooms.forEach(room => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "room-item";
        button.dataset.room = room;

        const hash = document.createElement("span");
        hash.className = "room-hash";
        hash.textContent = "#";

        const label = document.createElement("span");
        label.textContent = room;

        button.append(hash, label);
        button.addEventListener("click", () => joinRoom(room));
        roomList.appendChild(button);
    });

    setActiveRoom(currentRoom);
}

roomList?.querySelectorAll(".room-item").forEach(button => {
    button.addEventListener("click", () => joinRoom(button.dataset.room));
});

socket.on("connect", () => {
    setConnectionStatus(true);
    socket.emit("join_room", { room: currentRoom });
});

socket.on("disconnect", () => setConnectionStatus(false));
socket.on("connect_error", () => setConnectionStatus(false));

socket.on("room_history", data => {
    if (!data || data.room.toLowerCase() !== currentRoom.toLowerCase()) return;

    currentRoom = data.room;
    if (roomTitle) roomTitle.textContent = currentRoom;

    clearMessages();
    if (Array.isArray(data.messages)) data.messages.forEach(addMessage);
    if (messagesArea) messagesArea.scrollTop = messagesArea.scrollHeight;
});

socket.on("new_message", addMessage);

socket.on("room_list", renderRoomList);

socket.on("room_created", data => {
    if (!data) return;

    if (!data.success) {
        showToast(data.message || "Could not create room.");
        return;
    }

    currentRoom = data.room;
    clearMessages();
    renderRoomList(data.rooms || ["General", data.room]);
    setActiveRoom(data.room);
    socket.emit("join_room", { room: data.room });
    showToast("Room created successfully!");
});

socket.on("chat_error", data => {
    showToast(typeof data === "string" ? data : (data?.message || "Something went wrong."));
});

socket.on("typing_status", data => {
    if (!typingStatus || !data || data.room !== currentRoom) return;
    if (data.username === currentUser) return;

    typingStatus.textContent = data.typing ? `${data.username} is typing...` : "";
    clearTimeout(typingHideTimer);

    if (data.typing) {
        typingHideTimer = setTimeout(() => {
            typingStatus.textContent = "";
        }, 2500);
    }
});

messageForm?.addEventListener("submit", event => {
    event.preventDefault();

    const message = messageInput.value.trim();
    if (!message) return;

    if (message.length > 2000) {
        showToast("Message must be 2000 characters or fewer.");
        return;
    }

    if (!socket.connected) {
        showToast("Not connected. Please wait.");
        return;
    }

    socket.emit("send_message", { room: currentRoom, message });
    messageInput.value = "";
    socket.emit("typing", { room: currentRoom, typing: false });
    messageInput.focus();
});

messageInput?.addEventListener("input", () => {
    if (!socket.connected) return;

    socket.emit("typing", {
        room: currentRoom,
        typing: Boolean(messageInput.value.trim())
    });

    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
        socket.emit("typing", { room: currentRoom, typing: false });
    }, 1000);
});

createRoomButton?.addEventListener("click", () => {
    const room = prompt("Enter a room name (1–30 characters):");
    if (room === null) return;

    const cleanRoom = room.trim();

    if (!/^[A-Za-z0-9 _-]{1,30}$/.test(cleanRoom)) {
        showToast("Use letters, numbers, spaces, _ or -.");
        return;
    }

    if (!socket.connected) {
        showToast("Please wait until you're connected.");
        return;
    }

    socket.emit("create_room", { room: cleanRoom });
});

emojiButton?.addEventListener("click", () => {
    emojiPicker?.classList.toggle("open");
    emojiPicker?.classList.toggle("hidden", !emojiPicker.classList.contains("open"));
});

emojiPicker?.querySelectorAll("button").forEach(button => {
    button.addEventListener("click", () => {
        if (messageInput) {
            messageInput.value += button.textContent;
            messageInput.focus();
        }

        emojiPicker.classList.remove("open");
        emojiPicker.classList.add("hidden");
    });
});

document.addEventListener("click", event => {
    if (
        emojiPicker &&
        emojiButton &&
        !emojiPicker.contains(event.target) &&
        !emojiButton.contains(event.target)
    ) {
        emojiPicker.classList.remove("open");
        emojiPicker.classList.add("hidden");
    }
});

setConnectionStatus(false);
updateEmptyState();
