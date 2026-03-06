from flask import Flask, request, jsonify, session, redirect, url_for
import requests
from datetime import datetime
import threading
import time

app = Flask(__name__)
app.secret_key = "super_secret_hackathon_key"

# ===== CONFIG =====
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxxfeSaPl7Vj0cu4nUYFfV9MUFLswI3luand710m2WhRLV9O2V8zF78xdWKS4K9VmGg5w/exec"
TELEGRAM_TOKEN = "8749087192:AAH5tkQh7Wvfo0jS8nzkLP8m9x1CwaM6HcA"
CHAT_ID = "1495865712"

# ===== MEDICINE SCHEDULE =====
schedule = {
    "B": "10:00",
    "A": "13:00"
}

tablet_status = {}

# ===== AI LOGIC =====
def get_next_tablet():
    now = datetime.now().strftime("%H:%M")
    for tablet, time_value in sorted(schedule.items(), key=lambda x: x[1]):
        if now <= time_value:
            return f"Your next tablet is {tablet} at {time_value}"
    return "All tablets for today are completed"

# ===== GOOGLE SHEET LOGGING =====
def log_tablet(tablet, status):
    tablet_status[tablet] = status
    data = {
        "tablet": tablet,
        "scheduled": schedule.get(tablet),
        "taken": datetime.now().strftime("%H:%M") if status == "Taken" else "Not Taken",
        "status": status
    }
    try:
        requests.post(GOOGLE_SCRIPT_URL, json=data)
    except:
        print("Failed to log to Google Sheets")

# ===== TELEGRAM ALERT =====
def send_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except:
        print("Failed to send Telegram alert")

# ===== REMINDER CHECKER THREAD =====
def reminder_checker():
    while True:
        now = datetime.now().strftime("%H:%M")
        for tablet, scheduled_time in schedule.items():
            # Reminder
            if now == scheduled_time and tablet_status.get(tablet) != "Taken":
                send_alert(f"Reminder: Time to take tablet {tablet} now!")
                tablet_status[tablet] = "Pending"
            # Auto mark missed after 2 minutes
            current_obj = datetime.strptime(now, "%H:%M")
            scheduled_obj = datetime.strptime(scheduled_time, "%H:%M")
            diff = (current_obj - scheduled_obj).total_seconds() / 60
            if 2 <= diff < 3 and tablet_status.get(tablet) != "Taken":
                log_tablet(tablet, "Missed")
                send_alert(f"Tablet {tablet} was missed!")
        time.sleep(60)

# ===================== ROUTES =====================

# ----- LOGIN -----
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "1234":
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return """
            <script>
            alert("Invalid credentials");
            window.location.href="/login";
            </script>
            """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - AI Medication Tracker</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light d-flex align-items-center" style="height:100vh;">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-4">
                    <div class="card shadow-lg">
                        <div class="card-body">
                            <h3 class="text-center mb-4">Caretaker Login</h3>
                            <form method="post">
                                <div class="mb-3">
                                    <input type="text" name="username" class="form-control" placeholder="Username" required>
                                </div>
                                <div class="mb-3">
                                    <input type="password" name="password" class="form-control" placeholder="Password" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">Login</button>
                            </form>
                        </div>
                    </div>
                    <p class="text-center text-muted mt-3">
                        AI-Based Medication Adherence System
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# ----- LOGOUT -----
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ----- HOME DASHBOARD -----
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    tablet_cards = ""
    for tablet, time_value in schedule.items():
        status = tablet_status.get(tablet, "Pending")
        if status == "Taken":
            badge = '<span class="badge bg-success">Taken</span>'
        elif status == "Missed":
            badge = '<span class="badge bg-danger">Missed</span>'
        else:
            badge = '<span class="badge bg-warning text-dark">Pending</span>'
        tablet_cards += f"""
        <div class="card mb-3 shadow-sm">
            <div class="card-body d-flex justify-content-between align-items-center">
                <div>
                    <h5>Tablet {tablet} {badge}</h5>
                    <p>Scheduled at {time_value}</p>
                </div>
                <div>
                    <button class="btn btn-success me-2"
                        onclick="fetch('/taken/{tablet}').then(()=>window.location.reload())">
                        Taken
                    </button>
                    <button class="btn btn-danger"
                        onclick="fetch('/missed/{tablet}').then(()=>window.location.reload())">
                        Missed
                    </button>
                </div>
            </div>
        </div>
        """

    # ===== HTML for HOME + Chatbot =====
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Medication Tracker</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
    <div class="container py-5">

        <div class="d-flex justify-content-between mb-4">
            <h2>AI Medication Tracker</h2>
            <a href="/logout" class="btn btn-outline-danger btn-sm">Logout</a>
        </div>

        <div class="card shadow mb-4">
            <div class="card-body">
                <h4>Add New Tablet</h4>
                <form action="/add" method="post" class="row g-3">
                    <div class="col-md-6">
                        <input type="text" class="form-control" name="tablet" placeholder="Tablet Name" required>
                    </div>
                    <div class="col-md-4">
                        <input type="time" class="form-control" name="time" required>
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary w-100">Add</button>
                    </div>
                </form>
            </div>
        </div>

        {tablet_cards}

        <!-- Chatbot Section -->
        <div class="card shadow mb-4">
            <div class="card-body">
                <h4>AI Chatbot</h4>
                <div id="chatbox" style="height:200px; overflow-y:auto; border:1px solid #ccc; padding:10px; margin-bottom:10px;"></div>
                <div class="input-group">
                    <input type="text" id="userMessage" class="form-control" placeholder="Type your message...">
                    <button class="btn btn-primary" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>

    </div>

    <script>
    function sendMessage() {{
        let msg = document.getElementById('userMessage').value;
        if (!msg) return;

        let chatbox = document.getElementById('chatbox');
        chatbox.innerHTML += '<div><b>You:</b> ' + msg + '</div>';
        
        fetch('/chat', {{
            method: 'POST',
            headers: {{'Content-Type':'application/json'}},
            body: JSON.stringify({{message: msg}})
        }})
        .then(response => response.json())
        .then(data => {{
            chatbox.innerHTML += '<div><b>Bot:</b> ' + data.reply + '</div>';
            chatbox.scrollTop = chatbox.scrollHeight;
        }});
        
        document.getElementById('userMessage').value = '';
    }}
    </script>

    </body>
    </html>
    """

# ----- ADD TABLET -----
@app.route("/add", methods=["POST"])
def add():
    tablet = request.form.get("tablet")
    time_value = request.form.get("time")
    schedule[tablet] = time_value
    tablet_status[tablet] = "Pending"
    return redirect(url_for("home"))

# ----- MARK TAKEN -----
@app.route("/taken/<tablet>")
def taken(tablet):
    log_tablet(tablet, "Taken")
    return jsonify({"message": "Logged as Taken"})

# ----- MARK MISSED -----
@app.route("/missed/<tablet>")
def missed(tablet):
    log_tablet(tablet, "Missed")
    send_alert(f"Alert! Tablet {tablet} was not taken.")
    return jsonify({"message": "Logged as Missed"})

# ----- ASK NEXT TABLET -----
@app.route("/ask")
def ask():
    return jsonify({"response": get_next_tablet()})

# ----- AI CHATBOT -----
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Please type a message!"})

    # Simple AI logic
    if "next tablet" in user_message.lower():
        reply = get_next_tablet()
    elif "schedule" in user_message.lower():
        reply = "Today's tablets:\n" + "\n".join([f"{t}: {v}" for t,v in schedule.items()])
    elif "hello" in user_message.lower() or "hi" in user_message.lower():
        reply = "Hello! How can I assist you with your medications today?"
    else:
        reply = "I'm here to help! You can ask about your next tablet or today's schedule."

    return jsonify({"reply": reply})

# ================= RUN SERVER =================
if __name__ == "__main__":
    reminder_thread = threading.Thread(target=reminder_checker)
    reminder_thread.daemon = True
    reminder_thread.start()
    app.run(debug=True)