import firebase_admin
from firebase_admin import credentials, firestore, auth
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize Firebase Admin + Firestore
cred = credentials.Certificate(BASE_DIR / "serviceAccount.json")
firebase_app = firebase_admin.initialize_app(cred)
fs_db = firestore.client(firebase_app)

# u = auth.get_user("LNlcpEnDJec1jiUuMPAh364E7Hy2")
# print("server custom claims:", u.custom_claims)