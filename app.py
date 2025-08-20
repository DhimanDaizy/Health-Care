from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import google.generativeai as genai
from datetime import datetime
import os, json
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = "your-secret-key"

# Configure Gemini API
genai.configure(api_key="AIzaSyDWCA58AtifqtKVpDDvhfBJlfsaioCKiEo")
model = genai.GenerativeModel("gemini-1.5-flash")

# File to store reports
REPORTS_FILE = "reports.json"

def load_reports():
    if os.path.exists(REPORTS_FILE):
        with open(REPORTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_report(report):
    reports = load_reports()
    reports.append(report)
    with open(REPORTS_FILE, "w") as f:
        json.dump(reports, f, indent=2)

# Landing page: Main Reception
@app.route('/')
@app.route('/main')
def main_page():
    return render_template("main.html")

@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/form-submit', methods=['POST'])
def form_submit():
    session['user_data'] = {
        "name": request.form.get("name"),
        "age": request.form.get("age"),
        "gender": request.form.get("gender"),
        "conditions": request.form.getlist("conditions"),
        "medications": request.form.get("medications"),
        "email": request.form.get("email")
    }
    return redirect(url_for('checkup'))

@app.route('/checkup')
def checkup():
    return render_template("checkup.html")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        symptoms = request.form.get("symptoms")
        user_data = session.get('user_data', {})
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        if not symptoms:
            return jsonify({"response": "Please describe your symptoms."})

        prompt = f"""
You are a healthcare assistant. A patient with the following details has submitted their symptoms:

- Name: {user_data.get('name')}
- Age: {user_data.get('age')}
- Gender: {user_data.get('gender')}
- Pre-existing conditions: {', '.join(user_data.get('conditions', []))}
- Medications: {user_data.get('medications')}
- Submitted at: {current_time}

Symptoms:
{symptoms}

Please provide:
1. Possible conditions (not a diagnosis)
2. Recommended precautions
3. Suggested medical tests
4. When to consult a doctor

Always include this disclaimer:
"Note: This is not professional medical advice. Consult a licensed healthcare provider for real diagnosis or treatment."
"""
        ai_response = model.generate_content(prompt).text

        session['symptoms'] = symptoms
        session['ai_response'] = ai_response

        # Store report
        report = {
            "timestamp": current_time,
            "user": user_data,
            "symptoms": symptoms,
            "ai_response": ai_response
        }
        save_report(report)

        return redirect(url_for('result'))

    except Exception as e:
        return jsonify({"response": f"An error occurred: {str(e)}"})

@app.route('/result')
def result():
    response = session.get('ai_response', "No response found.")
    return render_template("result.html", response=response)

@app.route('/generate-report')
def generate_report():
    user = session.get('user_data', {})
    symptoms = session.get('symptoms', '')
    response = session.get('ai_response', '')
    return render_template("health_report.html", user=user, symptoms=symptoms, ai_response=response)

@app.route('/download-report')
def download_report():
    user = session.get('user_data', {})
    symptoms = session.get('symptoms', '')
    response = session.get('ai_response', '')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.multi_cell(0, 10, f"SmartCare Health Report\n\nPatient Name: {user.get('name')}\nAge: {user.get('age')}\nGender: {user.get('gender')}\nConditions: {', '.join(user.get('conditions', []))}\nMedications: {user.get('medications')}\n\nSymptoms:\n{symptoms}\n\nAI Health Assistant Response:\n{response}")

    pdf_path = "health_report.pdf"
    pdf.output(pdf_path)

    return send_file(pdf_path, as_attachment=True)

@app.route('/admin')
def admin():
    reports = load_reports()
    return render_template("admin.html", reports=reports)

if __name__ == '__main__':
    app.run(debug=True)
