import os
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from threading import Lock
import tempfile

# ---------- File Paths ----------
BASE_DIR = os.path.dirname(__file__)
USER_CSV_PATH = os.path.join(BASE_DIR, "users.csv")
PATIENT_CSV_PATH = os.path.join(BASE_DIR, "data", "tbm_data.csv")

# Lock for thread/process safety when writing
_csv_lock = Lock()


# ---------- Helpers ----------
def _atomic_to_csv(df: pd.DataFrame, path: str):
    """
    Safely write DataFrame to CSV by writing to a temp file first,
    then replacing the original file atomically.
    """
    dir_ = os.path.dirname(path)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_, newline="") as tmp:
        tmp_path = tmp.name
        df.to_csv(tmp_path, index=False)
    os.replace(tmp_path, path)


# ---------- Data Loaders ----------
def load_user_data():
    """Load all users from CSV (fresh each call)."""
    if not os.path.exists(USER_CSV_PATH):
        # Create file if it doesn’t exist
        pd.DataFrame(columns=["username", "password", "role"]).to_csv(USER_CSV_PATH, index=False)
    return pd.read_csv(USER_CSV_PATH)


def load_patient_data():
    """Load patient dataset from CSV."""
    if not os.path.exists(PATIENT_CSV_PATH):
        raise FileNotFoundError(f"Patient data file not found: {PATIENT_CSV_PATH}")
    return pd.read_csv(PATIENT_CSV_PATH)


# ---------- User Management ----------
def get_patient_data_by_id(df, patient_id):
    """Filter patient record by Patient_ID (string safe)."""
    df["Patient_ID"] = df["Patient_ID"].astype(str)
    return df[df["Patient_ID"] == str(patient_id)]


def register_user(username, password, role="client"):
    """
    Register new user with hashed password.
    Returns True if successful, False if username exists.
    """
    with _csv_lock:
        df = load_user_data()
        if username in df["username"].values:
            return False  # Username already exists

        hashed_password = generate_password_hash(password)
        new_user = pd.DataFrame([{
            "username": username,
            "password": hashed_password,
            "role": role
        }])
        updated_df = pd.concat([df, new_user], ignore_index=True)
        _atomic_to_csv(updated_df, USER_CSV_PATH)
        return True


def validate_user(username, password):
    """
    Validate login credentials.
    Returns (True, role) if valid, else (False, None).
    """
    df = load_user_data()
    user = df[df["username"] == username]
    if user.empty:
        return False, None  # No such user

    stored_hash = user.iloc[0]["password"]
    if check_password_hash(stored_hash, password):
        return True, user.iloc[0]["role"]
    return False, None
