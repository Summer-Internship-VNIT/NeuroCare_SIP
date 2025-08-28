"""
routes/__init__.py
All Flask routes for the TBM dashboard
"""

from pyexpat import model
from flask import render_template, request, redirect, session, url_for
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
from utils import load_user_data, load_patient_data, get_patient_data_by_id
import pandas as pd
import os, uuid
import joblib
from model.predictor import predict_condition
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from model.predictor import predict_condition
from flask import send_file
from fpdf import FPDF
from flask import current_app
from flask import Flask, render_template, request, redirect, url_for, send_file, current_app

app = Flask(__name__)
app.secret_key = "2345"  # replace with a secure random key




USER_CSV            = "users.csv"                      # username | password | role | patient_id
TBM_DATA_CSV        = os.path.join("data", "tbm_data.csv")

model_path = os.path.join(os.getcwd(), "model", "rf_csf_model.pkl")
model = joblib.load(model_path)


# --------------------------------------------------------------------------- #
#  ROUTES
# --------------------------------------------------------------------------- #


def init_routes(app):
    # ─────────────────────────── HOME ─────────────────────────── #
    @app.route("/home")
    def home():
        return render_template("home.html")

    @app.route("/")  # root → /home
    def index():
        return redirect(url_for("home"))

    # ────────────────────────── LOGIN ────────────────────────── #
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            users = load_user_data()
            username = request.form["username"]
            password = request.form["password"]

            row = users[users["username"] == username]
            if row.empty or not check_password_hash(row.iloc[0]["password"], password):
                return render_template("login.html", error="Invalid credentials")

            # Set session values
            session["username"] = username
            session["role"] = row.iloc[0]["role"]

            if row.iloc[0]["role"] == "Client":
                session["patient_id"] = row.iloc[0].get("patient_id")

            # Redirect based on role
            if session["role"] == "Admin":
                return redirect(url_for("admin_ui"))
            else:
                return redirect(url_for("data_entry"))

        return render_template("login.html")


    # ────────────────────────── Admin UI ────────────────────────── #
    # @app.route("/admin_ui", methods=["GET", "POST"])
    # def admin_ui():
    #     import pandas as pd
    #     import os

    #     data_path = os.path.join("data", "tbm_data.csv")

    #     if not os.path.exists(data_path):
    #         pred_summary = {}
    #         tbm_score_dist = {}
    #         total_records = 0
    #         total_patients = 0
    #     else:
    #         df = pd.read_csv(data_path)
    #         df = df.dropna(subset=["Diagnosis", "TBM Score", "Patient_ID"])

    #         # Get diagnosis counts
    #         df["Diagnosis"] = df["Diagnosis"].str.strip().str.capitalize()
    #         pred_summary = df["Diagnosis"].value_counts().to_dict()

    #         # Ensure both keys exist with default 0 if missing
    #         for label in ["Normal", "Abnormal"]:
    #             if label not in pred_summary:
    #                 pred_summary[label] = 0

    #         # Convert keys and values to string and int explicitly
    #         pred_summary = {str(k): int(v) for k, v in pred_summary.items()}

    #         # TBM Score distribution
    #         tbm_score_dist = df["TBM Score"].astype(str).value_counts().sort_index().to_dict()
    #         tbm_score_dist = {str(k): int(v) for k, v in tbm_score_dist.items()}

    #         total_records = len(df)
    #         total_patients = df["Patient_ID"].nunique()

    #     return render_template(
    #         "admin_ui.html",
    #         pred_summary=pred_summary,
    #         tbm_score_dist=tbm_score_dist,
    #         total_records=total_records,
    #         total_patients=total_patients
    #     )
    
    @app.route("/admin_ui", methods=["GET", "POST"])
    def admin_ui():
        import pandas as pd
        import os

        data_path = os.path.join("data", "tbm_data.csv")

        if not os.path.exists(data_path):
            pred_summary = {}
            tbm_score_dist = {}
            total_records = 0
            total_patients = 0
        else:
            df = pd.read_csv(data_path)
            df = df.dropna(subset=["Diagnosis", "TBM Score", "Patient_ID"])

            # Clean diagnosis text
            df["Diagnosis"] = df["Diagnosis"].str.strip().str.capitalize()

            # Map all non-normal diagnoses to "Abnormal"
            df["Label"] = df["Diagnosis"].apply(lambda x: "Normal" if x == "Normal" else "Abnormal")

            # Get counts for pie chart
            pred_summary = df["Label"].value_counts().to_dict()
            pred_summary = {str(k): int(v) for k, v in pred_summary.items()}

            # TBM Score distribution
            tbm_score_dist = df["TBM Score"].astype(str).value_counts().sort_index().to_dict()
            tbm_score_dist = {str(k): int(v) for k, v in tbm_score_dist.items()}

            total_records = len(df)
            total_patients = df["Patient_ID"].nunique()

        return render_template(
            "admin_ui.html",
            pred_summary=pred_summary,
            tbm_score_dist=tbm_score_dist,
            total_records=total_records,
            total_patients=total_patients
        )


    # ───────────────────────── SIGN-UP ───────────────────────── #
    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            role     = request.form["role"]

            users = load_user_data()
            if username in users["username"].values:
                return render_template("signup.html", error="Username already exists.")

            # Generate patient_id for clients
            patient_id = (
                request.form.get("patient_id") or str(uuid.uuid4())
                if role == "Client" else ""
            )

            # Store user
            hashed_pw = generate_password_hash(password)
            new_user  = pd.DataFrame(
                [{"username": username, "password": hashed_pw,
                  "role": role, "patient_id": patient_id}]
            )
            users = pd.concat([users, new_user], ignore_index=True)
            users.to_csv(USER_CSV, index=False)

            # Start session and redirect
            session.update(username=username, role=role, patient_id=patient_id)
            return redirect(url_for("login"))


        return render_template("signup.html")
    
     # ───────────────────── BLOG ───────────────────── # 
    @app.route('/blog')
    def blog():
        return render_template('blog.html')


 # ───────────── DATA-ENTRY (CSF) ───────────── #
    @app.route("/data_entry", methods=["GET", "POST"])
    def data_entry():
        if "username" not in session or session["role"] != "Client":
            return redirect(url_for("login"))

        if request.method == "POST":
            cols = [
                "Sr No.", "Date", "Sample Code", "Patient_ID",
                "TLC", "L%", "P%", "Sugar", "Protein",
                "Diagnosis", "TBM Score"
            ]

            # Load existing data or create new DataFrame
            df = (
                pd.read_csv(TBM_DATA_CSV)
                if os.path.exists(TBM_DATA_CSV) else pd.DataFrame(columns=cols)
            )

            # Prepare new row input
            next_sr = len(df) + 1
            patient_id = session["patient_id"]  # <-- Always use session value!
            new_row = {
                "Sr No.": next_sr,
                "Date": request.form["date"],
                "Sample Code": request.form["sample_code"],
                "Patient_ID": patient_id,  # <-- Use session, not form!
                "TLC": float(request.form["tlc"]),
                "L%": float(request.form["l_percent"]),
                "P%": float(request.form["p_percent"]),
                "Sugar": float(request.form["sugar"]),
                "Protein": float(request.form["protein"])
            }

            # 🔍 Predict Diagnosis & TBM Score
            prediction = predict_condition(new_row)
            new_row["Diagnosis"] = prediction.get("condition", "N/A")
            new_row["TBM Score"] = prediction.get("tbm_score", "N/A")

            # Append and save
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(TBM_DATA_CSV, index=False)

            return redirect(url_for("client_dashboard"))

        return render_template("data_entry.html")
    
     # ───────────────────── CLIENT DASHBOARD ───────────────────── #
    @app.route("/client_dashboard")
    def client_dashboard():
        if "username" not in session:
            return redirect(url_for("login"))

        role = session["role"]
        lab_df = load_patient_data()

        if role == "Admin":
            return render_template(
                "admin_dashboard.html",
                data=lab_df.to_dict(orient="records")
            )

        # Client dashboard
        pid = session["patient_id"]
        lab_rows = get_patient_data_by_id(lab_df, pid).to_dict(orient="records")

        # Final prediction for latest test
        if lab_rows:
            latest = lab_rows[-1]
            prediction = predict_condition(latest)
            diagnosis_label = prediction.get("condition", "N/A")
            model_output_percentage = prediction.get("tbm_score", "N/A")

            # 🛠️ Replace 'Abnormal' with 'TBM' only
            if diagnosis_label == "Abnormal":
                diagnosis_label = "TBM"

            # ✅ Always interpret the score
            diagnosis_message = interpret_tbm_score(model_output_percentage)

        else:
            diagnosis_label = ""
            model_output_percentage = ""
            diagnosis_message = ""

        return render_template(
            "client_dashboard.html",
            data=lab_rows,
            diagnosis_label=diagnosis_label,
            model_output_percentage=model_output_percentage,
            diagnosis_message=diagnosis_message
        )

    

      # ───────────────────── ADMIN DASHBOARD ───────────────────── #

    @app.route('/admin_dashboard')
    def admin_dashboard():
        try:
            df = pd.read_csv(TBM_DATA_CSV)  # Ensure TBM_DATA_CSV is defined
        except FileNotFoundError:
            return "TBM data file not found", 404

        df = df.dropna(subset=['Patient_ID', 'Diagnosis'])

        data = df.to_dict(orient="records")  # Convert to list of dicts for template

        return render_template('admin_dashboard.html', data=data)
    
    
    
    
    # ───────────────────── ADMIN_REPORT ───────────────────── # 
    @app.route('/admin_generate_report', methods=['POST'])
    def admin_generate_report():
        patient_id = request.form.get('patient_id')
        if not patient_id:
            return "Please enter a Patient ID.", 400

        return redirect(url_for('admin_report', patient_id=patient_id))

    
    @app.route('/admin_report/<patient_id>')
    def admin_report(patient_id):
        df = pd.read_csv(os.path.join('data', 'tbm_data.csv'))
        patient_data = df[df['Patient_ID'].astype(str) == str(patient_id)]

        if patient_data.empty:
            return f"<h3>No records found for Patient ID {patient_id}</h3>"

        return render_template("admin_report.html", records=patient_data.to_dict(orient='records'), patient_id=patient_id)

   
    

    # ───────────────────── CLIENT REPORT ───────────────────── #
    @app.route('/report')
    def report():
        if "username" not in session or session["role"] != "Client":
            return redirect(url_for("login"))

        pid = session.get("patient_id")
        try:
            df = load_patient_data()
            df = df[df["Patient_ID"] == pid]

            if df.empty:
                return render_template("report.html", record={})

            # Ensure date parsing works and handles missing/invalid formats
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"])
            df = df.sort_values(by="Date")

            # Handle case where Date column had all invalid entries
            if df.empty:
                return render_template("report.html", record={})

            latest_record = df.iloc[-1].fillna("N/A").to_dict()

            return render_template("report.html", record=latest_record)

        except Exception as e:
            print(f"[ERROR: /report] {e}")
            return render_template("report.html", record={})

    
    # ───────────────────── Download Report PDF ───────────────────── #
    @app.route('/download_report_pdf')
    def download_report_pdf():
        import time
        if "username" not in session or session["role"] != "Client":
            return redirect(url_for("login"))

        pid = session.get("patient_id")
        df = load_patient_data()

        df = df[df["Patient_ID"] == pid]
        if df.empty:
            return "No records found for this patient", 404

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

        latest_idx = df["Date"].idxmax()
        latest_record = df.loc[latest_idx].fillna("N/A")

        print("[DEBUG] Latest record for PDF:", latest_record.to_dict())  # ✅ Debug

        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Patient TBM Report", ln=1, align='C')
        pdf.ln(10)

        for col in ['Patient_ID', 'Date', 'Sample Code', 'TLC', 'L%', 'P%', 'Sugar', 'Protein', 'Diagnosis', 'TBM Score']:
            value = latest_record[col] if col in latest_record else "N/A"
            pdf.cell(200, 10, txt=f"{col}: {value}", ln=1)

        pdf_path = f"latest_report_{int(time.time())}.pdf"
        pdf.output(pdf_path)

        return send_file(pdf_path, as_attachment=True)




 # ───────────────────── Admin_PDF_Download───────────────────── # 

    @app.route('/admin_download_report_pdf/<patient_id>')
    def admin_download_report_pdf(patient_id):
        csv_path = os.path.join('data', 'tbm_data.csv')
        if not os.path.exists(csv_path):
            return "Data file not found.", 404

        df = pd.read_csv(csv_path)
        patient_data = df[df['Patient_ID'] == patient_id]

        if patient_data.empty:
            return f"No records found for Patient ID {patient_id}", 404

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Helper to clean/encode text safely
        def clean_text(text):
            if pd.isna(text):
                return "N/A"
            return str(text).replace('—', '-').encode('latin-1', errors='ignore').decode('latin-1')

        for _, row in patient_data.iterrows():
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="Patient TBM Report", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.ln(5)

            # Add each row of information
            for col in ['Patient_ID', 'Date', 'Sample Code', 'TLC', 'L%', 'P%', 'Sugar', 'Protein', 'Diagnosis', 'TBM Score']:
                value = clean_text(row[col]) if col in row else 'N/A'
                pdf.cell(200, 10, txt=f"{col}: {value}", ln=True)

            pdf.ln(5)

            # Diagnosis interpretation
            if row['Diagnosis'] == 'Abnormal':
                pdf.set_text_color(255, 0, 0)
                pdf.multi_cell(0, 10, clean_text(interpret_tbm_score(row['TBM Score'])))
            else:
                pdf.set_text_color(0, 128, 0)
                pdf.multi_cell(0, 10, clean_text("Diagnosis is Normal. No signs of TBM."))

            pdf.set_text_color(0, 0, 0)  # Reset text color

        # Save to file
        pdf_path = os.path.join('downloads', f'report_{patient_id}.pdf')
        os.makedirs('downloads', exist_ok=True)
        pdf.output(pdf_path)

        return send_file(pdf_path, as_attachment=True)


    # TBM interpretation logic
    def interpret_tbm_score(score):
        try:
            score = float(score)
        except:
            return "TBM Score is invalid."

        if score == 0:
            return "Score 0 — No evidence of TBM. Correlate clinically."
        elif score == 2.5:
            return "Score 2.5 — Mild CSF changes. Observation advised."
        elif score == 5:
            return "Score 5 — Possible TBM. Further evaluation needed."
        elif score == 7.5:
            return "Score 7.5 — Probable TBM. Immediate clinical action advised."
        elif score == 10:
            return "Score 10 — Strong TBM indication. Urgent action required."
        else:
            return "Score is unusual. Please consult a specialist."


    # ───────────────────── LOGOUT ───────────────────── # 
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("home"))