from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import joblib
import re
import numpy as np
import datetime
from fpdf import FPDF
import io

app = Flask(__name__)
CORS(app)

# ✅ Load your trained model and vectorizer
model = joblib.load("model/svm_stress_model.joblib")
vectorizer = joblib.load("model/tfidf_vectorizer.joblib")

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

LEVEL_TEXT = {
    0: "Absolutely No Stress – good in everything",
    1: "Calm & Balanced – good in mood check",
    2: "Energetic / Active Person – lifestyle problem",
    3: "Mild Stress – bad in your story",
    4: "Moderate Stress – bad lifestyle and bad in your story",
    5: "High Stress – bad in 4 parts"
}

def combine_fields(d):
    parts = [
        d.get("description", ""), d.get("lifestyle", ""), d.get("lately", ""),
        d.get("mood", ""), d.get("reflection", ""), d.get("stressCauses", ""),
        d.get("handling", ""), d.get("worries", ""), d.get("extra", "")
    ]
    return " ".join([p for p in parts if p])

@app.route("/predict", methods=["POST"])
def predict_stress():
    data = request.get_json()
    text = clean_text(combine_fields(data))
    if not text:
        return jsonify({"error": "No text provided"}), 400

    vec = vectorizer.transform([text])
    pred = int(model.predict(vec)[0])
    conf = float(model.predict_proba(vec).max()) * 100

    def suggestions_for(level):
        if level == 0:
            return ["Maintain your healthy balance.", "Keep positive habits going!"]
        elif level == 1:
            return ["Stay calm & mindful.", "Continue managing small stressors."]
        elif level == 2:
            return ["Take breaks between activities.", "Stay consistent with sleep."]
        elif level == 3:
            return ["Try journaling your stress.", "Practice deep breathing."]
        elif level == 4:
            return ["Reorganize tasks.", "Focus on one thing at a time."]
        else:
            return ["Seek support if needed.", "Talk to a friend or counselor."]

    recs = suggestions_for(pred)

    response = {
        "level": pred,
        "stressLevel": f"{pred} - {LEVEL_TEXT.get(pred, 'Unknown')}",
        "confidence": f"{conf:.2f}%",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "recommendations": recs
    }

    return jsonify(response)

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    data = request.get_json()

    # ✅ Helper to clean unsupported characters
    def safe_text(s):
        if not s:
            return ""
        replacements = {
            "–": "-", "—": "-", "‘": "'", "’": "'",
            "“": '"', "”": '"', "•": "*", "…": "...",
            "é": "e", "á": "a", "ó": "o", "ú": "u"
        }
        s = str(s)
        for k, v in replacements.items():
            s = s.replace(k, v)
        return s

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # --------------------------
    # HEADER
    # --------------------------
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "------------------------------------------------------------", ln=True, align="C")
    pdf.cell(0, 10, "STRESS ANALYSIS REPORT", ln=True, align="C")
    pdf.cell(0, 10, "------------------------------------------------------------", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "I", 12)
    pdf.cell(0, 8, f"Generated: {safe_text(data.get('timestamp', ''))}", ln=True, align="C")
    pdf.ln(8)

    # --------------------------
    # SECTION 1: SUMMARY
    # --------------------------
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, safe_text(f"Stress Level: {data.get('stressLevel','')}"), ln=True)
    pdf.cell(0, 8, safe_text(f"Model Confidence: {data.get('confidence','')}"), ln=True)
    pdf.ln(6)

    # --------------------------
    # SECTION 2: OBSERVATIONS
    # --------------------------
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Observations", ln=True)
    pdf.set_font("Arial", "", 12)

    level = int(data.get("level", 0))
    if level <= 1:
        obs = "You appear to be calm and emotionally balanced. Keep maintaining your current habits and mental well-being."
    elif level == 2:
        obs = "You are active and energetic, but small lifestyle habits may be adding mild stress. Keep a regular rest schedule."
    elif level == 3:
        obs = "Your responses suggest early signs of stress. Try identifying minor triggers and maintaining a consistent routine."
    elif level == 4:
        obs = "Your responses suggest that stress is affecting multiple areas. You may be struggling with time balance or emotional fatigue."
    else:
        obs = "Your responses indicate high stress across several areas. Please prioritize self-care and seek professional or social support if needed."

    pdf.multi_cell(0, 8, safe_text(obs))
    pdf.ln(6)

    # --------------------------
    # SECTION 3: RECOMMENDATIONS
    # --------------------------
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Personalized Recommendations", ln=True)
    pdf.set_font("Arial", "", 12)

    recs = data.get("recommendations", [])
    if recs:
        for r in recs:
            pdf.multi_cell(0, 8, f"* {safe_text(r)}")
    else:
        pdf.multi_cell(0, 8, "No specific recommendations available.")
    pdf.ln(8)

    # --------------------------
    # NOTE SECTION
    # --------------------------
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "------------------------------------------------------------", ln=True)
    pdf.cell(0, 10, "NOTE:", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(
        0, 8,
        safe_text("This is an AI-generated indicative result, not a clinical diagnosis.\n"
                  "If you experience prolonged stress or emotional distress, consider reaching out to a mental health professional.")
    )
    pdf.cell(0, 10, "------------------------------------------------------------", ln=True)

    # ✅ Safe final encoding
    pdf_bytes = bytes(pdf.output(dest="S").encode("latin1", "replace"))

    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name="Stress_Analysis_Report.pdf",
        mimetype="application/pdf"
    )
@app.route("/")
def home():
    return {"message": "SVM model backend running successfully!"}

# ✅ Run app — keep this LAST
if __name__ == "__main__":
    app.run(port=5000, debug=True)
