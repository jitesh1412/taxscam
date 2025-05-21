# 🧾 GST Scam Detector

A simple web application that detects potential GST billing inconsistencies or fraud from scanned or photographed bills using OCR (Optical Character Recognition). Built using Python (Flask) for the backend and vanilla HTML/CSS/JS for the frontend.

---

## 🔍 Features

- ✅ Extracts text from uploaded bill images using `pytesseract`
- 🔐 Detects valid/invalid **GSTINs**
- 📈 Identifies common **CGST + SGST combinations**
- 💸 Verifies valid **GST rates** (0%, 5%, 12%, 18%, 28%)
- 🧾 Confirms presence of **'Tax Invoice'**
- ⚖️ Checks **CGST and SGST balance**
