import os
<<<<<<< Updated upstream
import sqlite3
import numpy as np
=======
>>>>>>> Stashed changes
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import cv2

# AI
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np
import cv2

app = Flask(__name__)
app.secret_key = "deepfake_secret_123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

<<<<<<< Updated upstream
# ── Load model once at startup ─────────────────────────────────────────
MODEL_PATH = "models/deepfake_model.h5"
model = load_model(MODEL_PATH)
print("✅ Model loaded successfully!")
=======
# ================= CLIP MODEL ================= #

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

clip_model.eval()

# ================= IMAGE ANALYSIS ================= #

def analyze_image(image_path):
    try:
        fake_score = 0.0
        real_score = 0.0

        img = Image.open(image_path).convert("RGB")
        cv_img = cv2.imread(image_path)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        h, w = gray.shape

        # ================= CLIP ================= #
        inputs = clip_processor(
            text=[
                "real photograph",
                "natural photo",
                "AI generated image",
                "digital art",
                "3d render",
                "perfect fantasy scene",
                "unrealistic landscape"
            ],
            images=img,
            return_tensors="pt",
            padding=True
        )

        with torch.no_grad():
            outputs = clip_model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1).numpy()[0]

        real_clip = probs[0] + probs[1]
        ai_clip = sum(probs[2:])

        fake_score += ai_clip * 9
        real_score += real_clip * 3

        texture = cv2.Laplacian(gray, cv2.CV_64F).var()
        noise = np.std(gray)

        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges) / (h * w)

        color_var = np.var(cv_img)

        # PERFECTION DETECTOR
        perfection_score = 0
        if texture < 15: perfection_score += 1
        if noise < 25: perfection_score += 1
        if edge_density < 0.02: perfection_score += 1
        if color_var < 500: perfection_score += 1

        if perfection_score >= 3:
            fake_score += 6

        if texture > 40 and noise > 30:
            real_score += 3

        unique_vals = len(np.unique(gray))

        if unique_vals < 80:
            fake_score += 2
        else:
            real_score += 1

        # EXTRA AI DETECTION
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1)

        if np.var(grad_x) + np.var(grad_y) < 50:
            fake_score += 2.5

        flipped = cv2.flip(gray, 1)
        if np.mean(np.abs(gray - flipped)) < 10:
            fake_score += 2

        if texture < 30 and noise < 30 and color_var > 700:
            real_score += 5

        total = fake_score + real_score + 1e-6

        fake_percent = int((fake_score / total) * 100 * 0.95)
        real_percent = 100 - fake_percent

        result = "Fake" if fake_score > real_score * 1.15 else "Real"

        return result, fake_percent, real_percent, os.path.basename(image_path)

    except Exception as e:
        print("Error:", e)
        return "Error", 50, 50, os.path.basename(image_path)


# ================= VIDEO ANALYSIS ================= #
def analyze_video(video_path):
    try:
        cap = cv2.VideoCapture(video_path)

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(frame_count // 25, 1)

        fake_score = 0.0
        real_score = 0.0

        prev_gray = None
        prev_frame = None

        motion_list = []
        texture_list = []
        color_list = []
        brightness_list = []
        frame_diff_list = []
        clip_scores = []

        count = 0
        current = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if current % step == 0:

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # -------- TEXTURE --------
                texture = cv2.Laplacian(gray, cv2.CV_64F).var()
                texture_list.append(texture)

                # -------- BRIGHTNESS --------
                brightness_list.append(np.mean(gray))

                # -------- MOTION --------
                if prev_gray is not None:
                    motion = np.mean(np.abs(gray - prev_gray))
                    motion_list.append(motion)

                # -------- FRAME DIFFERENCE --------
                if prev_frame is not None:
                    frame_diff = np.mean(np.abs(frame - prev_frame))
                    frame_diff_list.append(frame_diff)

                # -------- COLOR CHANGE --------
                if prev_frame is not None:
                    color_diff = np.mean(np.abs(frame - prev_frame))
                    color_list.append(color_diff)

                # -------- CLIP CHECK (LOW WEIGHT) --------
                temp_path = "temp_frame.jpg"
                cv2.imwrite(temp_path, frame)
                _, fake, real, _ = analyze_image(temp_path)

                fake_score += fake * 0.05
                real_score += real * 0.08
                clip_scores.append(fake)

                prev_gray = gray
                prev_frame = frame

                count += 1

            current += 1

        cap.release()

        if count == 0:
            return "Error", 50, 50

        # ================= 🔴 AI DETECTION ================= #

        ai_flags = 0

        if len(motion_list) > 0:
            if np.std(motion_list) < 1.2:
                ai_flags += 1

        if len(texture_list) > 0:
            if np.std(texture_list) < 3:
                ai_flags += 1

        if len(frame_diff_list) > 0:
            if np.mean(frame_diff_list) < 2:
                ai_flags += 1

        if len(color_list) > 0:
            if np.std(color_list) < 1.5:
                ai_flags += 1

        if len(brightness_list) > 0:
            if np.std(brightness_list) < 2:
                ai_flags += 1

        if len(clip_scores) > 0:
            if np.std(clip_scores) < 4 and np.mean(clip_scores) > 60:
                ai_flags += 1

        # 🔥 STRONG AI DECISION
        if ai_flags >= 3:
            fake_score += 40
        elif ai_flags == 2:
            fake_score += 20

        # ================= 🟢 REAL DETECTION ================= #

        real_flags = 0

        if len(motion_list) > 0:
            if np.mean(motion_list) > 2.5:
                real_flags += 1

        if len(texture_list) > 0:
            if np.std(texture_list) > 8:
                real_flags += 1

        if len(frame_diff_list) > 0:
            if np.mean(frame_diff_list) > 5:
                real_flags += 1

        if len(brightness_list) > 0:
            if np.std(brightness_list) > 4:
                real_flags += 1

        if len(color_list) > 0:
            if np.std(color_list) > 2.5:
                real_flags += 1

        # 🔥 REAL DECISION
        if real_flags >= 2:
            real_score += 35
        elif real_flags == 1:
            real_score += 15

        # ================= ⚖️ SMART BALANCE ================= #

        # slight real-world bias
        real_score += 8

        # correction layer
        if fake_score > real_score and real_flags >= 2:
            fake_score *= 0.7

        if real_score > fake_score and ai_flags >= 3:
            real_score *= 0.7

        # if very close → stabilize
        if abs(fake_score - real_score) < 10:
            real_score += 5

        # ================= 🎯 NORMALIZATION ================= #

        total = fake_score + real_score + 1e-6

        fake_percent = (fake_score / total) * 100
        fake_percent = round(fake_percent, 1)

        # clamp realistic range
        fake_percent = max(5, min(95, fake_percent))
        real_percent = 100 - fake_percent

        # ================= FINAL RESULT ================= #

        if fake_percent > real_percent * 1.1:
            result = "Fake"
        else:
            result = "Real"

        return result, int(fake_percent), int(real_percent)

    except Exception as e:
        print("Video Error:", e)
        return "Error", 50, 50



# ================= DATABASE ================= #
>>>>>>> Stashed changes

# ── Database setup ─────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
<<<<<<< Updated upstream
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
=======

>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
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
=======

# ================= ROUTES ================= #

@app.route("/")
def home():
    return render_template("home.html")

>>>>>>> Stashed changes

# ── DASHBOARD ──────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
<<<<<<< Updated upstream
    if "user" not in session:
        return redirect("/login")
=======
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM history")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM history WHERE result='Fake'")
    fake = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM history WHERE result='Real'")
    real = cursor.fetchone()[0]

    conn.close()

    return render_template("dashboard.html", total=total, fake=fake, real=real)


# ================= IMAGE ================= #

@app.route("/detect_image", methods=["GET", "POST"])
def detect_image():
    if request.method == "POST":

        file = request.files["image"]

        if file.filename == "":
            return "No file selected"

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        result, fake, real, filename = analyze_image(filepath)

        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO history(filename,filetype,result,fake_percent,real_percent,date)
        VALUES (?,?,?,?,?,?)
        """, (file.filename, "Image", result, fake, real, date))

        conn.commit()
        conn.close()

        return render_template("result.html", filename=filename, result=result, fake=fake, real=real)

    return render_template("detect_image.html")


# ================= VIDEO ================= #

@app.route("/detect_video", methods=["GET", "POST"])
def detect_video():
    if request.method == "POST":

        file = request.files["video"]

        if file.filename == "":
            return "No file selected"

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        result, fake, real = analyze_video(filepath)

        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO history(filename,filetype,result,fake_percent,real_percent,date)
        VALUES (?,?,?,?,?,?)
        """, (file.filename, "Video", result, fake, real, date))

        conn.commit()
        conn.close()

        return render_template("result.html", filename=file.filename, result=result, fake=fake, real=real)

    return render_template("detect_video.html")


# ================= HISTORY ================= #

@app.route("/history")
def history():
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
# ── RUN ────────────────────────────────────────────────────────────────
=======

@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM history WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/history")


@app.route("/logout")
def logout():
    return redirect("/")


# ================= RUN ================= #

>>>>>>> Stashed changes
if __name__ == "__main__":
    app.run(debug=True) 