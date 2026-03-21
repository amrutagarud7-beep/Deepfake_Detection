from flask import Flask, render_template, request, redirect
import sqlite3
import os
import random
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    # HISTORY TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        filetype TEXT,
        result TEXT,
        fake_percent INTEGER,
        real_percent INTEGER,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ---------------- #

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect("/dashboard")
        else:
            return "Invalid Username or Password"

    return render_template("login.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ---------------- IMAGE DETECTION ---------------- #

@app.route("/detect_image", methods=["GET","POST"])
def detect_image():

    if request.method == "POST":

        file = request.files["image"]
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # FAKE AI RESULT
        fake = random.randint(10, 90)
        real = 100 - fake
        result = "Fake" if fake > real else "Real"

        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO history(filename,filetype,result,fake_percent,real_percent,date)
        VALUES (?,?,?,?,?,?)
        """, (file.filename, "Image", result, fake, real, date))

        conn.commit()
        conn.close()

        return redirect("/history")

    return render_template("detect_image.html")


# ---------------- VIDEO DETECTION ---------------- #

@app.route("/detect_video", methods=["GET","POST"])
def detect_video():

    if request.method == "POST":

        file = request.files["video"]
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        fake = random.randint(10, 90)
        real = 100 - fake
        result = "Fake" if fake > real else "Real"

        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO history(filename,filetype,result,fake_percent,real_percent,date)
        VALUES (?,?,?,?,?,?)
        """, (file.filename, "Video", result, fake, real, date))

        conn.commit()
        conn.close()

        return redirect("/history")

    return render_template("detect_video.html")


# ---------------- HISTORY ---------------- #

@app.route("/history")
def history():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM history ORDER BY id DESC")
    data = cursor.fetchall()

    conn.close()

    return render_template("history.html", data=data)


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)