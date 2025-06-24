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
            users     = load_user_data()
            username  = request.form["username"]
            password  = request.form["password"]

            row = users[users["username"] == username]
            if row.empty or not check_password_hash(row.iloc[0]["password"], password):
                return render_template("login.html", error="Invalid credentials")

            # Save minimal session
            session["username"]   = username
            session["role"]       = row.iloc[0]["role"]
            session["patient_id"] = row.iloc[0]["patient_id"]

            # Redirect logic
            if session["role"] == "Admin":
                return redirect(url_for("dashboard"))
            else:
                return redirect(url_for("data_entry"))

        return render_template("login.html")

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


    # ───────────── DATA-ENTRY (CSF) ───────────── #
    @app.route("/data_entry", methods=["GET", "POST"])
    def data_entry():
        if "username" not in session or session.get("role") != "Client":
            print("❌ Unauthorized access.")
            return redirect(url_for("login"))

        if request.method == "POST":
            try:
                print("📥 Received form:", dict(request.form))
                print("🔑 Session:", session)
                print("📄 Saving to:", TBM_DATA_CSV)

                # Full expected columns, including optional ones
                columns = [
                    "Sr No.", "Date", "Sample Code", "Patient_ID",
                    "TLC", "L%", "P%", "Sugar", "Protein",
                    "Diagnosis", "TBM Score"
                ]

                # Ensure folder exists
                os.makedirs(os.path.dirname(TBM_DATA_CSV), exist_ok=True)

                # Load or initialize DataFrame
                if os.path.exists(TBM_DATA_CSV):
                    df = pd.read_csv(TBM_DATA_CSV)
                    # Ensure all columns exist
                    for col in columns:
                        if col not in df.columns:
                            df[col] = ""
                else:
                    df = pd.DataFrame(columns=columns)

                # New row entry
                next_sr = len(df) + 1
                new_row = {
                    "Sr No.": next_sr,
                    "Date": request.form["date"],
                    "Sample Code": request.form["sample_code"],
                    "Patient_ID": session.get("patient_id", "UNKNOWN"),
                    "TLC": request.form["tlc"],
                    "L%": request.form["l_percent"],
                    "P%": request.form["p_percent"],
                    "Sugar": request.form["sugar"],
                    "Protein": request.form["protein"],
                    "Diagnosis": "",
                    "TBM Score": ""
                }

                print("➕ Adding new row:", new_row)

                # Add to DataFrame
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(TBM_DATA_CSV, index=False)
                print("✅ CSV updated successfully!")

                return redirect(url_for("dashboard"))

            except Exception as e:
                print("❌ Exception while saving:", e)

        return render_template("data_entry.html")



    # ───────────────────── DASHBOARD ───────────────────── #
    # @app.route("/dashboard")
    # def dashboard():
    #     if "username" not in session:
    #         return redirect(url_for("login"))

    #     role   = session["role"]
    #     lab_df = load_patient_data()

    #     if role == "Admin":
    #         return render_template(
    #             "admin_dashboard.html",
    #             data=lab_df.to_dict(orient="records")
    #         )

    #     # Client dashboard
    #     pid      = session["patient_id"]
    #     lab_rows = get_patient_data_by_id(lab_df, pid).to_dict(orient="records")

    #     return render_template("client_dashboard.html", data=lab_rows)

    @app.route('/admin/dashboard')
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

    # ───────────────────── BLOG ───────────────────── # 
    @app.route('/blog')
    def blog():
        return render_template('blog.html')

    # ───────────────────── RECORDS ───────────────────── # 
    @app.route("/dashboard")
    def dashboard():
        if "username" not in session:
            return redirect(url_for("login"))

        role = session["role"]
        data = load_patient_data()

        # ─── Admin Dashboard ───
        # if role == "Admin":
        #     return render_template("admin_dashboard.html", data=data.to_dict(orient="records"))
        
         # ─── Admin Dashboard ───
        if role == "Admin":
            try:
                df = pd.read_csv(TBM_DATA_CSV)
            except FileNotFoundError:
                return "TBM data file not found", 404

            # Drop incomplete records for accurate stats
            df = df.dropna(subset=['Patient_ID', 'Diagnosis'])

            # Basic stats
            total_records = len(df)
            total_patients = df['Patient_ID'].nunique()
            diagnosis_counts = df['Diagnosis'].value_counts().to_dict()

            # TBM Score Distribution (only for abnormal cases)
            tbm_df = df[df['Diagnosis'] == 'Abnormal'].dropna(subset=['TBM Score'])
            tbm_score_dist = (
                tbm_df['TBM Score']
                .astype(str)
                .value_counts()
                .sort_index()
                .to_dict()
            )

            return render_template(
                "admin_ui.html",
                total_records=total_records,
                total_patients=total_patients,
                pred_summary=diagnosis_counts,
                tbm_score_dist=tbm_score_dist
            )

        # ─── Client Dashboard ───
        pid = session["patient_id"]
        patient_df = get_patient_data_by_id(data, pid)

        # ✅ Sort records by Date (latest last)
        if not patient_df.empty:
            patient_df["Date"] = pd.to_datetime(patient_df["Date"], errors='coerce')
            patient_df = patient_df.dropna(subset=["Date"])
            patient_df = patient_df.sort_values(by="Date")

        lab_rows = patient_df.to_dict(orient="records")
        prediction = {}
        updated = False

        # ✅ Add Diagnosis & TBM Score if not already present
        for i, row in enumerate(lab_rows):
            pred_result = predict_condition(row)
            if "Diagnosis" not in row or "TBM Score" not in row \
                or row.get("Diagnosis") != pred_result.get("condition") \
                or row.get("TBM Score") != pred_result.get("tbm_score"):
                row["Diagnosis"] = pred_result.get("condition", "N/A")
                row["TBM Score"] = pred_result.get("tbm_score", "N/A")
                updated = True

        # ✅ Save updated rows to CSV only if changes were made
        if updated:
            updated_df = pd.DataFrame(lab_rows)
            full_data = load_patient_data()

            # Remove old rows for this patient, replace with updated
            full_data = full_data[full_data["Patient_ID"] != pid]
            full_data = pd.concat([full_data, updated_df], ignore_index=True)
            full_data.to_csv(TBM_DATA_CSV, index=False)

        # ✅ Final prediction for latest test
        if lab_rows:
            prediction = predict_condition(lab_rows[-1])

        return render_template("client_dashboard.html", data=lab_rows, prediction=prediction)

   # ───────────────────── Report ───────────────────── # 
    @app.route('/report')
    def report():
        if "username" not in session:
            return redirect(url_for("login"))

        pid = session.get("patient_id")
        data = load_patient_data()
        patient_df = get_patient_data_by_id(data, pid)

        # Sort to get latest record
        if not patient_df.empty:
            patient_df["Date"] = pd.to_datetime(patient_df["Date"], errors="coerce")
            patient_df = patient_df.dropna(subset=["Date"])
            patient_df = patient_df.sort_values(by="Date")
            latest_record = patient_df.iloc[-1].to_dict()
        else:
            latest_record = {}

        return render_template("report.html", record=latest_record)
    
    # ───────────────────── Download Report PDF ───────────────────── #
    @app.route('/download_report_pdf')
    def download_report_pdf():
        df = pd.read_csv(os.path.join('data', 'tbm_data.csv'))
        latest_record = df.iloc[-1]

        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Patient TBM Report", ln=1, align='C')
        pdf.ln(10)

        for col in ['Patient_ID', 'Date', 'Sample Code', 'TLC', 'L%', 'P%', 'Sugar', 'Protein', 'Diagnosis', 'TBM Score']:
            value = latest_record[col] if col in latest_record else "N/A"
            pdf.cell(200, 10, txt=f"{col}: {value}", ln=1)

        pdf_path = "latest_report.pdf"
        pdf.output(pdf_path)

        return send_file(pdf_path, as_attachment=True)

 # ───────────────────── Admin_PDF_Download───────────────────── # 

    from flask import send_file, request
    import pandas as pd
    from fpdf import FPDF

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