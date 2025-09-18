import firebase_admin
from firebase_admin import credentials, firestore, auth as fa
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize Firebase Admin + Firestore
cred = credentials.Certificate(BASE_DIR / "serviceAccount.json")
firebase_app = firebase_admin.initialize_app(cred)
fs_db = firestore.client(firebase_app)

# u = auth.get_user("LNlcpEnDJec1jiUuMPAh364E7Hy2")
# print("server custom claims:", u.custom_claims)

# replace with the UID shown in your response (localId)
uid = "wooohzQgBxURhTVWvJabOGPl6vt1"

# read current server-side custom claims
u = fa.get_user(uid)
print("custom_claims:", u.custom_claims)   # None or dict

# to set claims (run once)
# fa.set_custom_user_claims(uid, {"role": "customer", "permissions": []})
# re-fetch to confirm
u2 = fa.get_user(uid)
print("after set:", u2.custom_claims)