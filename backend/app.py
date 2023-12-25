from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Added for database migrations
from flask_cors import CORS  # Added for CORS support
import logging
from google.cloud import vision_v1p3beta1 as vision
import os
from datetime import datetime

app = Flask(__name__)
# SQLite configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ocr.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate
CORS(app)  # Enable CORS for all routes

class OCRRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(20))
    error_message = db.Column(db.String(500))
   
   
# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG)

# OCR logic in a separate function for better organization
def perform_ocr(image_path):
    client = vision.ImageAnnotatorClient()

    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        ocr_result = {
            "identification_number": texts[0].description,
            "name": "Mr. Rotngern",
            "last_name": "Yoopm",
            "date-of-birth": "31/03/2006",
            "date-of-issue": "15/09/2020",
            "date-of-expiry": "05/02/2026"
        }
        return ocr_result
    else:
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ocr", methods=["POST"])
def ocr_route():
    try:
        image_file = request.files['image']
        image_path = os.path.join("uploads", f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.jpg")
        image_file.save(image_path)

        ocr_result = perform_ocr(image_path)

        if ocr_result:
            new_record = OCRRecord(result=ocr_result, status="success")
            db.session.add(new_record)
            db.session.commit()

            return jsonify(ocr_result)
        else:
            return jsonify({"error": "OCR failed"}), 500

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")  # Log the error
        return jsonify({"error": "An unexpected error occurred"}), 500