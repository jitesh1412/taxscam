import os
import cv2
import pytesseract
import re
from collections import Counter
from flask import Flask, request, jsonify, send_from_directory
import tempfile

app = Flask(__name__, static_folder='static')

pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

def extract_text_from_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Image not found or unreadable.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return text

def check_gstin(text):
    gstin_pattern = r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}\b"
    gstins = re.findall(gstin_pattern, text)
    return gstins if gstins else ["❌ No GSTIN found"]

def check_gst_rate(text):
    VALID_RATES = {'0%', '5%', '12%', '18%', '28%'}
    found_rates = re.findall(r'\b\d{1,2}(?:\.\d+)?%', text)

    if not found_rates:
        return "❌ No GST rate found"

    rate_counts = Counter(found_rates)

    valid_combinations = {
        ('2.5%', '2.5%'): '5%',
        ('6%', '6%'): '12%',
        ('9%', '9%'): '18%',
        ('14%', '14%'): '28%'
    }

    for (r1, r2), final in valid_combinations.items():
        if rate_counts[r1] >= 1 and rate_counts[r2] >= 1:
            return f"✅ CGST + SGST combo: {r1} + {r2} = {final} (valid)"

    unique_rates = set(found_rates)
    invalid_rates = [r for r in unique_rates if r not in VALID_RATES]
    valid_rates = [r for r in unique_rates if r in VALID_RATES]

    if valid_rates:
        return f"✅ Valid GST rate(s): {', '.join(valid_rates)}"
    else:
        return f"⚠️ Invalid GST rate(s): {', '.join(invalid_rates)}"

def check_tax_invoice(text):
    return "✅ 'Tax Invoice' found" if 'tax invoice' in text.lower() else "❌ 'Tax Invoice' not found"

def check_cgst_sgst_balance(text):
    cgst = re.search(r'CGST\s*[:\-\|]?\s*₹?\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    sgst = re.search(r'SGST\s*[:\-\|]?\s*₹?\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)

    if cgst and sgst:
        cgst_val = float(cgst.group(1))
        sgst_val = float(sgst.group(1))
        if abs(cgst_val - sgst_val) <= 0.1:
            return "✅ CGST and SGST are balanced"
        else:
            return f"⚠️ CGST and SGST mismatch: CGST={cgst_val}, SGST={sgst_val}"

    amounts = re.findall(r'₹?\s*(\d+(?:\.\d+)?)', text)
    amounts = [float(a) for a in amounts]
    count = Counter(amounts)
    balanced_amounts = [amt for amt, c in count.items() if c >= 2]

    if balanced_amounts:
        return f"✅ Possible balanced CGST and SGST amount detected"
    else:
        return "⚠️ CGST and SGST not clearly found or balanced"

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify(error="No image file part in the request"), 400

    image_file = request.files['image']

    if image_file.filename == '':
        return jsonify(error="No selected file"), 400

    # Use tempfile to handle concurrency safely
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        image_file.save(tmp_filename)

    try:
        text = extract_text_from_image(tmp_filename)
        result = {
            "Extracted Text": text,
            "GSTIN": check_gstin(text),
            "GST Rate": check_gst_rate(text),
            "Invoice Type": check_tax_invoice(text),
            "CGST/SGST": check_cgst_sgst_balance(text)
        }
    except Exception as e:
        os.remove(tmp_filename)
        return jsonify(error=str(e)), 500

    os.remove(tmp_filename)
    return jsonify(result)

if __name__ == '__main__':
    # host='0.0.0.0' allows LAN access, remove it if not needed
    app.run(debug=True, host='0.0.0.0')
