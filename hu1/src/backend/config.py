import os
from dotenv import load_dotenv

load_dotenv()


def _lista(valor, sep=","):
    return tuple(x.strip().lower() for x in valor.split(sep) if x.strip())


class Config:
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "serviceAccountKey.json")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_WEB = {
        "apiKey": os.getenv("FIREBASE_WEB_API_KEY", ""),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
        "appId": os.getenv("FIREBASE_WEB_APP_ID", ""),
    }
    DOMINIOS_UCO = _lista(os.getenv("DOMINIOS_UCO", "uco.es,red.uco.es"))
    CORS_ORIGINS = [o for o in os.getenv("CORS_ORIGINS", "http://localhost:5000").split(",") if o]
    LOGIN_URL = os.getenv("LOGIN_URL", "/login.html")
    REDIRECT_DELAY_MS = int(os.getenv("REDIRECT_DELAY_MS", "5000"))
