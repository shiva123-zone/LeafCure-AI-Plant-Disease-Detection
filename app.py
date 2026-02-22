from utils.pdf_generator import generate_pdf
from flask import send_file
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session, send_file
import os
import cv2
import numpy as np
import tensorflow as tf
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from functools import wraps
import json
from datetime import datetime
from pymongo import MongoClient
from PIL import Image

# =========================
# Flask App Config
# =========================
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# =========================
# MongoDB
# =========================
client = MongoClient("mongodb://localhost:27017/")
db = client["leafcure"]
users_col = db["users"]
detect_col = db["detections"]

# =========================
# Firebase
# =========================
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# =========================
# Model Paths
# =========================
SAVEDMODEL_DIR = "models/LeafCure_SavedModel"
CLASS_JSON_PATH = "models/class_indices.json"

model = None
infer = None
CLASS_NAMES = []
plant_validator = None

# =========================
# 🔥 Disease Treatments
# =========================
DISEASE_TREATMENTS = {
    "Tomato Early blight": {
        "chemical": "Spray Mancozeb or Chlorothalonil every 7–10 days",
        "organic": "Neem oil spray or compost tea",
        "prevention": "Avoid overhead irrigation and rotate crops"
    },
    "Potato - Early blight": {
        "chemical": "Use Mancozeb or Copper-based fungicide",
        "organic": "Neem oil or baking soda spray",
        "prevention": "Remove infected leaves and ensure proper spacing"
    },
    "Tomato Septoria leaf spot": {
        "chemical": "Apply Chlorothalonil fungicide",
        "organic": "Garlic extract or neem oil spray",
        "prevention": "Remove infected debris and avoid wet foliage"
    },
    "Healthy": {
        "chemical": "No chemical treatment required",
        "organic": "Maintain soil nutrition",
        "prevention": "Regular monitoring"
    }
}
# =========================
# 🛒 MEDICINE DATABASE
# =========================
MEDICINE_DB = {

    "Tomato Early blight": [
        {
            "name": "Mancozeb Fungicide",
            "price": 350,
            "link": "https://www.amazon.in/s?k=mancozeb+fungicide"
        },
        {
            "name": "Neem Oil Spray",
            "price": 200,
            "link": "https://www.amazon.in/s?k=neem+oil+spray"
        }
    ],

    "Potato - Early blight": [
        {
            "name": "Copper Fungicide",
            "price": 300,
            "link": "https://www.amazon.in/s?k=copper+fungicide"
        }
    ],

    "Tomato Septoria leaf spot": [
        {
            "name": "Chlorothalonil Spray",
            "price": 400,
            "link": "https://www.amazon.in/s?k=chlorothalonil"
        }
    ],

    "Healthy": [
        {
            "name": "Organic Compost",
            "price": 150,
            "link": "https://www.amazon.in/s?k=organic+compost"
        }
    ]
}


# =========================
# Load AI Models
# =========================
def load_ai_model():
    global model, infer, CLASS_NAMES, plant_validator

    model = tf.saved_model.load(SAVEDMODEL_DIR)
    infer = model.signatures["serving_default"]
    print("✅ Disease Model Loaded")

    with open(CLASS_JSON_PATH, "r") as f:
        class_dict = json.load(f)

    CLASS_NAMES = [None] * len(class_dict)
    for name, idx in class_dict.items():
        CLASS_NAMES[idx] = name

    print("✅ Disease Classes Loaded")

    plant_validator = MobileNetV2(weights="imagenet", include_top=True)
    print("✅ Plant Image Validator Loaded")

# =========================
# Soft Image Validation
# =========================
def is_plant_image(filepath):
    try:
        img = cv2.imread(filepath)
        return img is not None
    except:
        return False

# =========================
# Auth Helpers
# =========================
def verify_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "No token"}), 401
        decoded = firebase_auth.verify_id_token(token)
        request.uid = decoded["uid"]
        return f(*args, **kwargs)
    return decorated

ADMIN_EMAILS = ["shivbabuchauhan348@gmail.com"]

def verify_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        decoded = firebase_auth.verify_id_token(token)
        if decoded.get("email") not in ADMIN_EMAILS:
            return jsonify({"error": "Admin only"}), 403
        return f(*args, **kwargs)
    return decorated

# =========================
# Pages
# =========================
@app.route('/')
def home(): return redirect(url_for("login_page"))

@app.route('/login')
def login_page(): return render_template("login.html")

@app.route('/register')
def register_page(): return render_template("register.html")

@app.route('/forgot-password')
def forgot_page(): return render_template("forgot.html")

@app.route('/dashboard')
def dashboard_page(): return render_template("dashboard.html")

@app.route('/detect')
def detect_page(): return render_template("detect.html")

@app.route('/download_report')
def download_report():

    user = session.get("user_email")
    disease = session.get("disease")
    confidence = session.get("confidence")
    image_path = session.get("image")

    # Safety Check
    if not disease or not confidence or not image_path:
        return "No analysis report found. Please detect a leaf first."

    pdf_path = generate_pdf(user, disease, confidence, image_path)

    return send_file(pdf_path, as_attachment=True)

# =========================
# Remedies API
# =========================
@app.route("/get_remedies")
def get_remedies():

    disease = session.get("disease")

    meds = MEDICINE_DB.get(disease, [
        {
            "name": "Consult Agriculture Expert",
            "price": 0,
            "link": "#"
        }
    ])

    return jsonify(meds)




@app.route('/history')
def history_page(): return render_template("history.html")
@app.route('/admin')
def admin_page():
    return render_template("admin.html")

@app.route('/profile')
def profile_page(): return render_template("profile.html")

# =========================
# Remedies Page
# =========================
@app.route('/remedies')
def remedies_page():
    return render_template("remedies.html")


@app.route("/api/admin/dashboard", methods=["GET"])
@verify_admin
def admin_dashboard_data():

    total_users = users_col.count_documents({})
    total_detections = detect_col.count_documents({})

    # Latest detections
    latest_detections = list(
        detect_col.find().sort("timestamp", -1).limit(10)
    )

    # Disease count
    pipeline = [
        {"$group": {"_id": "$disease", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    disease_stats = list(detect_col.aggregate(pipeline))

    # Daily scans
    daily_pipeline = [
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$timestamp"
                    }
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    daily_stats = list(detect_col.aggregate(daily_pipeline))

    for d in latest_detections:
        d["_id"] = str(d["_id"])
        d["timestamp"] = d["timestamp"].isoformat()

    return jsonify({
        "success": True,
        "total_users": total_users,
        "total_detections": total_detections,
        "latest_detections": latest_detections,
        "disease_stats": disease_stats,
        "daily_stats": daily_stats
    })

# =========================
# Uploads
# =========================
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# =========================
# 🔥 Prediction API (FIXED + TREATMENT)
# =========================
@app.route("/api/predict", methods=["POST"])
def predict():
    if infer is None:
        return jsonify({"error": "Model not loaded"}), 500

    file = request.files.get("file")
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    if not is_plant_image(filepath):
        os.remove(filepath)
        return jsonify({"error": "Invalid plant image"}), 400

    img = cv2.imread(filepath)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224))
    img = img / 255.0
    img = np.expand_dims(img, axis=0).astype(np.float32)

    output = infer(tf.constant(img))
    result = list(output.values())[0].numpy()

    class_idx = np.argmax(result[0])
    confidence = float(result[0][class_idx] * 100)

    disease = CLASS_NAMES[class_idx].replace("___", " - ").replace("_", " ")
    # =========================
    # SAVE RESULT FOR PDF REPORT
    # =========================
    session["disease"] = disease
    session["confidence"] = f"{confidence:.2f}"

    # Save image full path
    session["image"] = filepath

    # Save user email from firebase
    token = request.headers.get("Authorization")
    if token:
        decoded = firebase_auth.verify_id_token(token)
        session["user_email"] = decoded.get("email")
    else:
        session["user_email"] = "guest_user"


    treatment = DISEASE_TREATMENTS.get(disease, {
        "chemical": "Consult agriculture expert",
        "organic": "Consult agriculture expert",
        "prevention": "Consult agriculture expert"
    })

    token = request.headers.get("Authorization")
    if token:
        decoded = firebase_auth.verify_id_token(token)
        detect_col.insert_one({
            "uid": decoded["uid"],
            "image": filename,
            "disease": disease,
            "confidence": confidence,
            "timestamp": datetime.utcnow()
        })

    return jsonify({
        "success": True,
        "disease": disease,
        "confidence": f"{confidence:.2f}%",
        "severity": "High" if confidence > 90 else "Medium" if confidence > 70 else "Low",
        "treatment": treatment
    })

# =========================
# History API (UNCHANGED)
# =========================
@app.route("/api/history", methods=["GET"])
@verify_token
def get_history():
    uid = request.uid
    history_list = list(detect_col.find({"uid": uid}).sort("timestamp", -1))

    for h in history_list:
        h["_id"] = str(h["_id"])
        h["timestamp"] = h["timestamp"].isoformat()

    return jsonify({"history": history_list})

# =========================
# Profile API (UNCHANGED)
# =========================
@app.route("/api/profile", methods=["GET"])
@verify_token
def get_profile():
    uid = request.uid

    # User info
    user = users_col.find_one({"uid": uid})
    if user:
        user["_id"] = str(user["_id"])
    else:
        user = {
            "uid": uid,
            "created_at": datetime.utcnow()
        }

    # Detection stats
    detections = list(
        detect_col.find({"uid": uid}).sort("timestamp", -1)
    )

    for d in detections:
        d["_id"] = str(d["_id"])
        if d.get("timestamp"):
            d["timestamp"] = d["timestamp"].isoformat()

    last_detection = detections[0] if detections else None

    return jsonify({
        "success": True,
        "user": user,
        "total_detections": len(detections),
        "last_detection": last_detection
    })

# =========================
# Main
# =========================
if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    load_ai_model()
    app.run(host="0.0.0.0", port=5000, debug=True)
