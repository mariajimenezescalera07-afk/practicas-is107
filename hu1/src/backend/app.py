import logging
import os

from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from firebase_client import init_firebase
from seguridad import requiere_admin
from services import registro as svc

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
logging.basicConfig(level=logging.INFO)


def create_app():
    init_firebase()
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    CORS(app, origins=Config.CORS_ORIGINS)
    limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")

    # ───────── Manejo de errores uniforme ─────────
    @app.errorhandler(svc.RegistroError)
    def _error_negocio(e):
        return jsonify({
            "error": {"codigo": e.codigo, "mensaje": e.mensaje, "detalles": e.detalles},
            "notificacion": svc.notificacion("error", "No se pudo completar la acción", e.mensaje),
        }), e.status

    @app.errorhandler(429)
    def _demasiadas(_):
        msg = "Has hecho demasiados intentos. Espera un minuto y vuelve a probar."
        return jsonify({"error": {"codigo": "rate_limit", "mensaje": msg},
                        "notificacion": svc.notificacion("aviso", "Demasiados intentos", msg)}), 429

    @app.errorhandler(500)
    def _interno(_):
        msg = "Ocurrió un error inesperado. Inténtalo de nuevo."
        return jsonify({"error": {"codigo": "interno", "mensaje": msg},
                        "notificacion": svc.notificacion("error", "Error del servidor", msg)}), 500

    # ───────── Frontend estático ─────────
    @app.get("/")
    def _inicio():
        return send_from_directory(FRONTEND_DIR, "index.html")

    # ───────── API pública ─────────
    @app.get("/api/health")
    def _health():
        return jsonify({"ok": True})

    @app.get("/api/config/firebase-web")
    def _config_web():
        return jsonify(Config.FIREBASE_WEB)

    @app.post("/api/registro")
    @limiter.limit("10 per minute")
    def _registro():
        cuerpo, status = svc.registrar_investigador(request.get_json(silent=True))
        return jsonify(cuerpo), status

    # ───────── API de administración ─────────
    @app.get("/api/admin/solicitudes")
    @requiere_admin
    def _listar():
        estado = request.args.get("estado", "pendiente")
        return jsonify({"solicitudes": svc.listar_solicitudes(estado, request.args.get("limite", 50))})

    @app.post("/api/admin/solicitudes/<solicitud_id>/aprobar")
    @requiere_admin
    def _aprobar(solicitud_id):
        cuerpo = request.get_json(silent=True) or {}
        return jsonify(svc.aprobar_solicitud(
            solicitud_id, g.admin_uid,
            forzar=cuerpo.get("forzar") is True,
            motivo_forzado=str(cuerpo.get("motivo", ""))))

    @app.post("/api/admin/solicitudes/<solicitud_id>/rechazar")
    @requiere_admin
    def _rechazar(solicitud_id):
        cuerpo = request.get_json(silent=True) or {}
        return jsonify(svc.rechazar_solicitud(solicitud_id, g.admin_uid, str(cuerpo.get("motivo", ""))))

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
