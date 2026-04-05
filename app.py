import os
import sqlite3
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import cv2

app = Flask(__name__)
app.secret_key = "deepfake_secret_123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Load model once at startup ─────────────────────────────────────────
MODEL_PATH = "models/deepfake_model.h5"
model = load_model(MODEL_PATH)
print("✅ Model loaded successfully!")

# ── Database setup ─────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            filetype TEXT,
            result TEXT,
            confidence TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ── Helper: predict image ──────────────────────────────────────────────
def predict_image(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    prediction = model.predict(img_array)[0][0]
    label = "REAL" if prediction < 0.5 else "FAKE"
    confidence = round((1 - prediction) * 100 if prediction < 0.5 else prediction * 100, 2)
    return label, confidence

# ── HOME ───────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("home.html")

# ── REGISTER ───────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form["name"]
        email    = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users VALUES (NULL,?,?,?,?)",
                           (name, email, username, password))
            conn.commit()
        except:
            conn.close()
            return render_template("register.html", error="Username already exists!")
        conn.close()
        return redirect("/login")
    return render_template("register.html")

# ── LOGIN ──────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session["user"] = username
            return redirect("/dashboard")
        return render_template("login.html", error="Invalid credentials!")
    return render_template("login.html")

# ── LOGOUT ─────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ── DASHBOARD ──────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM history")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM history WHERE result='FAKE'")
    fake  = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM history WHERE result='REAL'")
    real  = cursor.fetchone()[0]
    conn.close()
    return render_template("dashboard.html", total=total, fake=fake, real=real)

# ── DETECT IMAGE ───────────────────────────────────────────────────────
@app.route("/detect", methods=["GET", "POST"])
def detect():
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            label, confidence = predict_image(filepath)
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO history VALUES (NULL,?,?,?,?,?)",
                           (file.filename, "Image", label, str(confidence), date))
            conn.commit()
            conn.close()
            return render_template("result.html",
                                   result=label,
                                   confidence=confidence,
                                   filename=file.filename)
    return render_template("detect_image.html")

# ── DETECT VIDEO ───────────────────────────────────────────────────────
@app.route("/detect-video", methods=["GET", "POST"])
def detect_video():
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            cap = cv2.VideoCapture(filepath)
            predictions = []
            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % 10 == 0:
                    frame_path = os.path.join(UPLOAD_FOLDER, "temp_frame.jpg")
                    cv2.imwrite(frame_path, frame)
                    label, confidence = predict_image(frame_path)
                    predictions.append(1 if label == "FAKE" else 0)
                frame_count += 1
            cap.release()
            if predictions:
                fake_ratio = sum(predictions) / len(predictions)
                label = "FAKE" if fake_ratio > 0.5 else "REAL"
                confidence = round(fake_ratio * 100 if fake_ratio > 0.5 else (1 - fake_ratio) * 100, 2)
            else:
                label, confidence = "UNKNOWN", 0
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO history VALUES (NULL,?,?,?,?,?)",
                           (file.filename, "Video", label, str(confidence), date))
            conn.commit()
            conn.close()
            return render_template("result.html",
                                   result=label,
                                   confidence=confidence,
                                   filename=file.filename)
    return render_template("detect_video.html")

# ── HISTORY ────────────────────────────────────────────────────────────
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template("history.html", data=data)

# ── RUN ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)