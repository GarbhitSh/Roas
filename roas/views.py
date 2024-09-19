import firebase_admin
from firebase_admin import credentials, firestore

# Use a service account
cred = credentials.Certificate('D:\\sih\\web dashboard\\roas\\dashboard\\a.json')
firebase_admin.initialize_app(cred)

db = firestore.client()