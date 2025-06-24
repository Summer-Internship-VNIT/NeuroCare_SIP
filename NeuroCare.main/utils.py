import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

USER_CSV_PATH = 'users.csv'
PATIENT_CSV_PATH = 'data/tbm_data.csv'

# Load user data from CSV
def load_user_data():
    return pd.read_csv(USER_CSV_PATH)

# Load patient data from CSV
def load_patient_data():
    return pd.read_csv(PATIENT_CSV_PATH)

# Get patient data by ID
def get_patient_data_by_id(df, patient_id):
    return df[df['Patient_ID'] == patient_id]

# Register new user with hashed password
def register_user(username, password, role='client'):
    df = load_user_data()
    if username in df['username'].values:
        return False  # Username already exists

    hashed_password = generate_password_hash(password)
    new_user = pd.DataFrame([{'username': username, 'password': hashed_password, 'role': role}])
    updated_df = pd.concat([df, new_user], ignore_index=True)
    updated_df.to_csv(USER_CSV_PATH, index=False)
    return True

# Validate user login credentials
def validate_user(username, password):
    df = load_user_data()
    user = df[df['username'] == username]
    if user.empty:
        return False, None  # No such user
    stored_hash = user.iloc[0]['password']
    if check_password_hash(stored_hash, password):
        return True, user.iloc[0]['role']
    return False, None
