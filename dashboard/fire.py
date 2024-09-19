from django.shortcuts import render
import firebase_admin
from firebase_admin import credentials, firestore

def connect():
    
    cred = credentials.Certificate('D:\\sih\\web dashboard\\roas\\dashboard\\a.json')
    firebase_admin.initialize_app(cred)

    return firestore.client()