"""Carga datos iniciales: un administrador y un padrón de ejemplo de perfiles UCO.
Uso:  python seed.py"""
import os

from firebase_admin import auth as fb_auth
from google.cloud import firestore as gcf

import config  # noqa: F401  (carga .env)
import constants as K
from firebase_client import get_db, init_firebase

PERFILES_EJEMPLO = [
    {"acreditacion": "UCO-0001", "nombre": "Ana Ruiz Molina", "email_institucional": "ana.ruiz@uco.es",
     "departamento": "Química Orgánica", "centro": "Facultad de Ciencias"},
    {"acreditacion": "UCO-0002", "nombre": "Luis Pérez Gil", "email_institucional": "luis.perez@uco.es",
     "departamento": "Bioquímica y Biología Molecular", "centro": "Facultad de Veterinaria"},
    {"acreditacion": "UCO-0003", "nombre": "Marta Serrano Díaz", "email_institucional": "marta.serrano@uco.es",
     "departamento": "Física Aplicada", "centro": "Facultad de Ciencias"},
]


def main():
    init_firebase()
    db = get_db()

    for p in PERFILES_EJEMPLO:
        db.collection(K.COL_PERFILES_UCO).document(p["acreditacion"]).set(
            {**p, "activo": True, "vinculado_a": None, "creado_en": gcf.SERVER_TIMESTAMP}, merge=True)
    print(f"{len(PERFILES_EJEMPLO)} perfiles UCO cargados.")

    email = os.environ["ADMIN_EMAIL"].lower()
    password = os.environ["ADMIN_PASSWORD"]
    try:
        usuario = fb_auth.get_user_by_email(email)
    except fb_auth.UserNotFoundError:
        usuario = fb_auth.create_user(email=email, password=password, display_name="Administrador")
    fb_auth.set_custom_user_claims(usuario.uid, {"rol": K.ROL_ADMIN})
    db.collection(K.COL_USUARIOS).document(usuario.uid).set({
        "uid": usuario.uid, "email": email, "nombre": "Administrador", "apellidos": "SG-CICT",
        "tipo": K.TIPO_UCO, "prioridad": K.PRIORIDAD_UCO, "rol": K.ROL_ADMIN,
        "estado": K.USUARIO_ACTIVO, "institucion": "Universidad de Córdoba",
        "creado_en": gcf.SERVER_TIMESTAMP}, merge=True)
    print(f"Administrador listo: {email}")


if __name__ == "__main__":
    main()
