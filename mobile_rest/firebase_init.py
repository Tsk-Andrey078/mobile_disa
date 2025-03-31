import os
import firebase_admin
from firebase_admin import credentials

SERVICE_ACCOUNT_PATH = os.path.join(os.path.dirname(__file__), "service-account.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)
