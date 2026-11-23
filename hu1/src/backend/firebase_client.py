import os

import firebase_admin
from firebase_admin import credentials, firestore

from config import Config


def init_firebase():
    if firebase_admin._apps:
        return
    ruta = Config.FIREBASE_CREDENTIALS
    if ruta and os.path.exists(ruta):
        cred = credentials.Certificate(ruta)
    else:
        cred = credentials.ApplicationDefault()
    opciones = {"projectId": Config.FIREBASE_PROJECT_ID} if Config.FIREBASE_PROJECT_ID else None
    firebase_admin.initialize_app(cred, opciones)


def get_db():
    return firestore.client()
