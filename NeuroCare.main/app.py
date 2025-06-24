from flask import Flask
from routes import init_routes  # if using modular routing
import os
import pickle
import numpy as np
from flask import Flask, render_template

# Define full path to the model
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'rf_csf_model.pkl')

# Load the model
with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)



app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure sessions

# Initialize routes
init_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
