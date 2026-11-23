from functools import wraps

from flask import g, jsonify, request
from firebase_admin import auth as fb_auth

import constants as K
from firebase_client import get_db


def _error(status, codigo, mensaje):
    return jsonify({
        "error": {"codigo": codigo, "mensaje": mensaje},
        "notificacion": {"tipo": "error", "titulo": "Acceso denegado", "mensaje": mensaje},
    }), status


def requiere_admin(f):
    """Exige un ID token de Firebase válido de un usuario con rol admin y estado activo."""
    @wraps(f)
    def envoltorio(*args, **kwargs):
        cabecera = request.headers.get("Authorization", "")
        if not cabecera.startswith("Bearer "):
            return _error(401, "sin_token", "Falta el token de autenticación.")
        try:
            decodificado = fb_auth.verify_id_token(cabecera[7:], check_revoked=True)
        except Exception:
            return _error(401, "token_invalido", "La sesión no es válida o ha caducado.")
        doc = get_db().collection(K.COL_USUARIOS).document(decodificado["uid"]).get()
        datos = doc.to_dict() if doc.exists else {}
        if datos.get("rol") != K.ROL_ADMIN or datos.get("estado") != K.USUARIO_ACTIVO:
            return _error(403, "no_admin", "Necesitas permisos de administrador.")
        g.admin_uid = decodificado["uid"]
        return f(*args, **kwargs)
    return envoltorio
