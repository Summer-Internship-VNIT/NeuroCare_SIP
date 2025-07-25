# NeuroCare
### AI-Powered Diagnostic System for Early Detection of Tuberculous Meningitis

Welcome to the **NeuroCare** repository. NeuroCare is an AI-driven clinical decision support tool designed to assist in the early detection of Tuberculous Meningitis (TBM) using Cerebrospinal Fluid (CSF) biomarker analysis. Developed as part of a Summer Internship Program at VNIT Nagpur, this project integrates machine learning, advanced data engineering, and full-stack web development to provide a deployable diagnostics platform for clinical environments.

## Introduction

**Tuberculous Meningitis (TBM)** is a severe condition that poses significant diagnostic challenges due to nonspecific symptoms and overlapping biomarker profiles. Timely, accurate diagnosis is essential to prevent fatal outcomes and long-term neurological complications.

**NeuroCare** is a comprehensive, AI-powered solution developed in collaboration with CIIMS Hospital & Research Center. The platform classifies CSF reports as "Normal" or "Abnormal" (suspected TBM), assigns a clinician-friendly TBM Severity Score, and offers real-time dashboards and automated PDF reporting for clinical workflows.

## Project Webpage
Access the live NeuroCare application and TBM Dashboard here: TBM Dashboard

## Features

- **Accurate TBM Classification** using clinically relevant CSF markers
- **Interpretable TBM Severity Score** (0–10 scale) for clinicians
- **Dual-role Web Application:** 
  - Operator: For data entry, individual report access
  - Admin: Full database access, analytics, and report export
- **Interactive Dashboards:** Trend analysis, immune profile visualizations, and patient follow-up
- **Automated PDF Report Generation** for standardized, shareable diagnostics
- **Secure User Management:** Encrypted login, session management, role-based routing

## Dataset Creation

- **Source:** Limited, anonymized records from CIIMS Hospital & Research Center
- **Approach:** Hybrid dataset with both real and synthetic CSF records
  - Synthetic data generated using clinical reference ranges for critical CSF biomarkers (TLC, lymphocytes %, polymorphs %, protein, sugar)
  - Data augmentation mimicked medical scenarios to enhance volume and diversity
  - **Final dataset:** 250 robust records (merged synthetic and augmented real)
- **Data Shape:** (37646, 6)
- **Class distribution:** Abnormal: 22,284 | Normal: 15,362

## Modeling Approach

Four supervised machine learning models were trained and evaluated:
- **Logistic Regression:** Strong baseline but limited by linear assumptions.
- **Random Forest Classifier:** Handled non-linear feature interactions, robust to outliers, highest interpretability.
- **Support Vector Machine (RBF Kernel):** Good for high-dimensional data but computationally intensive.
- **XGBoost Classifier:** High performance with boosting, sensitive to noise.

Models were evaluated by accuracy, precision, recall, F1-score, and confusion matrix.

## Performance & Results

- **Best Model:** Random Forest (accuracy 94.5%), saved as `rf_csf_model.pkl` for deployment.
- **TBM Score:** A rule-based enhancement for interpretability (0—no TBM; 10—critical TBM; increments of 2.5).

## Application Overview

- **Backend:** Python Flask
- **Frontend:** Jinja2-based HTML templates, Chart.js for visualizations
- **User Roles:** 
  - **Operator:** Enter patient data, access/save personal reports, visualize trends
  - **Admin:** Database access, generate/export any patient report, analytics dashboard

### Key Features

- Role-based dashboards with clinical and population-level analytics
- Secure authentication (hashed credentials in `users.csv`)
- Data persistence in `tbm_data.csv`
- Downloadable PDF diagnostic reports (FPDF)

## How to Use

1. **Clone the repo and set up Python environment**
2. **Install dependencies:**  
   ```
   pip install -r requirements.txt
   ```
3. **Run the web application:**  
   ```
   python app.py
   ```
4. **Log in** as Operator or Admin
5. **Enter CSF test data, retrieve diagnostic predictions, and download PDF reports**

## Project Structure

```
model/
  └── predictor.py, rf_csf_model.pkl
routes/
  └── __init__.py (APIs/app logic)
templates/
  └── HTML frontend (data_entry.html, admin_dashboard.html, etc.)
static/
  └── CSS, JS, images for dashboards and UI
users.csv
tbm_data.csv
app.py
```

## Challenges

- **Limited Real Data:** Required synthetic augmentation for robust training
- **Class Imbalance:** Tailored design to reflect real clinical distributions
- **Model Interpretability:** Balanced clinical trust with predictive performance
- **Deployment Complexity:** Integrated authentication, reporting, and real-time dashboarding

## Future Work

- Live integration with Electronic Health Records (EHR)
- Diagnosis support for other CNS infections, expansion to deep learning models
- Multilingual support, voice input, mobile-first UI improvements
- Larger-scale clinical validation trials

## Contributors

- Aarya Raut (IV Year, CSE AIML, RCOEM)
- Sakshi Parate (IV Year, CSE AIML, RCOEM)
- Sanjeev Gour (IV Year, CSE AIML, RCOEM)
- Aman Patne (IV Year, CSE AIML, RCOEM)
- Guided by Dr. Shital Raut (Associate Professor, VNIT)

## Acknowledgments

- **Visvesvaraya National Institute of Technology (VNIT) Nagpur**
- **CIIMS Hospital & Research Center, Nagpur** for clinical collaborations and anonymized data support

*For more details on methodology and deployment, please see the project documentation and the full report in the repo.*

[1] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/64201438/5a4a30c7-ca2d-4139-9388-b1b233daac40/SIP-Project-Report-VNIT.pdf
