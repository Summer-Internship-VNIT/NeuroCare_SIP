import numpy as np
import joblib
import os

# Dynamically load model regardless of working directory
model_path = os.path.join(os.path.dirname(__file__), "rf_csf_model.pkl")
model = joblib.load(model_path)

def predict_condition(latest_record):
    """
    Predicts CSF condition and evaluates TBM scoring.
    Input: latest_record (dict with keys: 'TLC', 'L%', 'P%', 'Sugar', 'Protein')
    Output: prediction dict with condition, tbm_score, and interpretation.
    """

    try:
        tlc     = float(latest_record['TLC'])
        lymp    = float(latest_record['L%'])
        poly    = float(latest_record['P%'])
        sugar   = float(latest_record['Sugar'])
        protein = float(latest_record['Protein'])
    except Exception:
        return {
            'condition': 'Unknown',
            'tbm_score': 'N/A',
            'interpretation': 'Invalid input values.'
        }

    # Prepare feature array for prediction
    features = np.array([[tlc, lymp, poly, sugar, protein]])
    
    # Run prediction
    try:
        pred = model.predict(features)[0]
        tbm_prob = model.predict_proba(features)[0][1] if hasattr(model, 'predict_proba') else None
    except Exception:
        return {
            'condition': 'Unknown',
            'tbm_score': 'N/A',
            'interpretation': 'Model prediction failed.'
        }

    # Base prediction result
    prediction = {
        'condition': 'Abnormal' if pred == 0 else 'Normal',
        'tbm_score': 'N/A',
        'interpretation': "No TBM, Kindly correlate clinically"
    }

    # Only apply TBM scoring if Abnormal
    if pred == 0:
        score = 0
        if tlc > 75 and 80 <= lymp <= 85:
            score += 5
        if 15 <= sugar <= 48:
            score += 2.5
        if 75 <= protein <= 200:
            score += 2.5

        if score == 2.5:
            interpretation = "Kindly correlate clinically"
        elif score == 5:
            interpretation = "Possible TBM, Kindly correlate clinically"
        elif score == 7.5:
            interpretation = "Probable TBM, Kindly correlate clinically"
        elif score == 10:
            interpretation = "Definite TBM, Kindly correlate clinically"
        else:
            interpretation = "No TBM, Kindly correlate clinically"

        prediction['tbm_score'] = score
        prediction['interpretation'] = interpretation

    return prediction
