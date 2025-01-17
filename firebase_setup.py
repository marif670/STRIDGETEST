import firebase_admin
from firebase_admin import credentials, initialize_app

# Firebase credentials path
firebase_credentials_path = "Firebase_Admin.json"

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials_path)
    initialize_app(cred)
