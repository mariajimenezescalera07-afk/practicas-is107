"""Lógica de negocio de la HU1: registro de investigadores con acreditación."""
import hashlib
import logging
import re
from urllib.parse import urlencode

from firebase_admin import auth as fb_auth
from google.cloud import firestore as gcf
from google.cloud.firestore_v1.base_query import FieldFilter

import constants as K
from config import Config
from firebase_client import get_db

log = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ACREDITACION_RE = re.compile(r"^[A-Za-z0-9._-]{3,40}$")


class RegistroError(Exception):
    def __init__(self, codigo, mensaje, status=400, detalles=None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.status = status
        self.detalles = detalles or {}


# ───────────────────────── utilidades ─────────────────────────
def normalizar_email(email):
    return (email or "").strip().lower()


def id_solicitud(email_norm):
    """ID determinista: una sola solicitud por email (evita duplicados por carreras)."""
    return hashlib.sha256(email_norm.encode("utf-8")).hexdigest()[:40]


def notificacion(tipo, titulo, mensaje):
    return {"tipo": tipo, "titulo": titulo, "mensaje": mensaje}


def _redirect_login(email, aviso):
    query = urlencode({"aviso": aviso, "email": email})
    return {"url": f"{Config.LOGIN_URL}?{query}", "espera_ms": Config.REDIRECT_DELAY_MS}


def _auditar(evento, **datos):
    try:
        get_db().collection(K.COL_AUDITORIA).add(
            {"evento": evento, **datos, "fecha": gcf.SERVER_TIMESTAMP}
        )
    except Exception:  # la auditoría nunca debe romper el flujo
        log.exception("No se pudo registrar el evento de auditoría %s", evento)


def _serializar(doc):
    datos = doc.to_dict() or {}
    datos["id"] = doc.id
    for clave, valor in list(datos.items()):
        if hasattr(valor, "isoformat"):
            datos[clave] = valor.isoformat()
    return datos


# ───────────────────────── validación ─────────────────────────
def validar_payload(data):
    if not isinstance(data, dict):
        raise RegistroError("payload_invalido", "Los datos enviados no son válidos.", 400)

    nombre = str(data.get("nombre", "")).strip()
    apellidos = str(data.get("apellidos", "")).strip()
    email = normalizar_email(str(data.get("email", "")))
    password = str(data.get("password", ""))
    es_uco = data.get("es_uco") is True
    acreditacion = str(data.get("acreditacion", "")).strip().upper()
    institucion = str(data.get("institucion", "")).strip()

    errores = {}
    if len(nombre) < 2:
        errores["nombre"] = "Escribe tu nombre."
    if len(apellidos) < 2:
        errores["apellidos"] = "Escribe tus apellidos."
    if not EMAIL_RE.match(email) or len(email) > 254:
        errores["email"] = "Escribe un correo electrónico válido."
    if len(password) < 10:
        errores["password"] = "La contraseña debe tener al menos 10 caracteres."
    if es_uco:
        if not ACREDITACION_RE.match(acreditacion):
            errores["acreditacion"] = "Indica tu número de acreditación UCO (3 a 40 caracteres, sin espacios)."
    elif len(institucion) < 2:
        errores["institucion"] = "Indica la institución a la que perteneces."
    if data.get("acepta_tratamiento") is not True:
        errores["acepta_tratamiento"] = "Debes aceptar el tratamiento de tus datos."

    if errores:
        raise RegistroError("validacion", "Revisa los campos marcados.", 422, errores)

    return {
        "nombre": nombre, "apellidos": apellidos, "email": email, "password": password,
        "es_uco": es_uco, "acreditacion": acreditacion if es_uco else None,
        "institucion": "Universidad de Córdoba" if es_uco else institucion,
    }


# ───────────────────── verificación institucional ─────────────────────
def verificar_perfil_uco(db, email, acreditacion):
    """Comprueba la acreditación contra el padrón `perfiles_uco`.
    Devuelve (perfil_id | None, resultado)."""
    if not acreditacion:
        return None, K.VERIF_NO_APLICA
    doc = db.collection(K.COL_PERFILES_UCO).document(acreditacion).get()
    if not doc.exists:
        return None, K.VERIF_NO_ENCONTRADA
    perfil = doc.to_dict()
    if not perfil.get("activo", False):
        return None, K.VERIF_INACTIVA
    if perfil.get("vinculado_a"):
        return None, K.VERIF_YA_VINCULADA
    email_padron = (perfil.get("email_institucional") or "").lower()
    dominio_ok = email.split("@")[-1] in Config.DOMINIOS_UCO
    if email != email_padron and not dominio_ok:
        return None, K.VERIF_EMAIL_NO_COINCIDE
    return doc.id, K.VERIF_VERIFICADA


# ───────────────────── cuenta de Firebase Auth ─────────────────────
def _preparar_cuenta_auth(email, password, nombre_completo):
    """Crea la cuenta DESHABILITADA hasta que un administrador apruebe la solicitud."""
    try:
        existente = fb_auth.get_user_by_email(email)
    except fb_auth.UserNotFoundError:
        return fb_auth.create_user(
            email=email, password=password, display_name=nombre_completo, disabled=True
        ).uid
    if not existente.disabled:
        # Cuenta activa sin ficha en `usuarios`: no la tocamos (evita tomar cuentas ajenas).
        raise RegistroError("cuenta_existente", "Ya existe una cuenta con este correo.", 409)
    fb_auth.update_user(existente.uid, password=password, display_name=nombre_completo, disabled=True)
    return existente.uid


# ───────────────────── HU1: registro ─────────────────────
def registrar_investigador(data):
    """Devuelve (cuerpo_json, status_http)."""
    db = get_db()
    datos = validar_payload(data)
    email = datos["email"]

    # 1) ¿Ya está registrado? → aviso informativo + redirección al login
    existe = (db.collection(K.COL_USUARIOS)
              .where(filter=FieldFilter("email", "==", email)).limit(1).get())
    if existe:
        _auditar("registro_usuario_existente", email=email)
        return _respuesta_ya_registrado(email), 409

    # 2) Determinar tipo y prioridad SIEMPRE en servidor (nunca fiarse del cliente)
    perfil_id, verificacion = verificar_perfil_uco(db, email, datos["acreditacion"])
    tipo = K.TIPO_UCO if verificacion == K.VERIF_VERIFICADA else K.TIPO_EXTERNO
    prioridad = K.PRIORIDAD_POR_TIPO[tipo]

    solicitud = {
        "email": email,
        "nombre": datos["nombre"],
        "apellidos": datos["apellidos"],
        "institucion": datos["institucion"],
        "acreditacion": datos["acreditacion"],
        "tipo_declarado": K.TIPO_UCO if datos["es_uco"] else K.TIPO_EXTERNO,
        "tipo": tipo,
        "prioridad": prioridad,
        "verificacion_uco": verificacion,
        "perfil_uco_id": perfil_id,
        "estado": K.ESTADO_PENDIENTE,
        "creado_en": gcf.SERVER_TIMESTAMP,
        "revisado_por": None,
        "revisado_en": None,
        "motivo_rechazo": None,
        "uid": None,
        "intentos": 1,
    }

    # 3) Crear la solicitud de forma atómica (idempotente ante dobles envíos)
    ref = db.collection(K.COL_SOLICITUDES).document(id_solicitud(email))

    @gcf.transactional
    def _crear(tx):
        snap = ref.get(transaction=tx)
        if snap.exists:
            actual = snap.to_dict()
            if actual["estado"] == K.ESTADO_PENDIENTE:
                return "en_curso", actual
            if actual["estado"] == K.ESTADO_APROBADA:
                return "ya_registrado", actual
            nueva = {**solicitud, "intentos": actual.get("intentos", 1) + 1}
            tx.set(ref, nueva)
            return "reabierta", nueva
        tx.set(ref, solicitud)
        return "creada", solicitud

    resultado, _ = _crear(db.transaction())

    if resultado == "ya_registrado":
        return _respuesta_ya_registrado(email), 409
    if resultado == "en_curso":
        return {
            "resultado": "solicitud_en_curso",
            "notificacion": notificacion(
                "aviso", "Tu solicitud ya está en revisión",
                "Ya recibimos tu solicitud. Te avisaremos cuando un administrador la revise."),
            "redirect": None,
        }, 200

    # 4) Cuenta de Auth deshabilitada hasta la aprobación
    try:
        uid = _preparar_cuenta_auth(email, datos["password"], f'{datos["nombre"]} {datos["apellidos"]}')
        ref.update({"uid": uid})
    except RegistroError:
        _deshacer_solicitud(ref, resultado)
        raise
    except Exception:
        log.exception("Error creando la cuenta de Firebase Auth")
        _deshacer_solicitud(ref, resultado)
        raise RegistroError("error_auth", "No pudimos crear tu solicitud. Inténtalo de nuevo en unos minutos.", 500)

    _auditar("registro_solicitud_creada", email=email, tipo=tipo, prioridad=prioridad, verificacion=verificacion)

    if tipo == K.TIPO_UCO:
        msg = ("Hemos verificado tu acreditación de la UCO. Tu solicitud tiene prioridad y "
               "un administrador la revisará en cuanto pueda.")
    elif datos["es_uco"]:
        msg = ("No pudimos verificar tu acreditación de la UCO automáticamente, así que un administrador "
               "revisará tu caso manualmente. Si ya eres investigador de la UCO, tu solicitud se atenderá "
               "con prioridad cuando se confirme.")
    else:
        msg = "Un administrador revisará tu solicitud y te avisaremos por correo."
    return {
        "resultado": "solicitud_creada",
        "tipo": tipo,
        "prioridad": prioridad,
        "verificacion_uco": verificacion,
        "notificacion": notificacion("exito", "Solicitud enviada", msg),
        "redirect": None,
    }, 201


def _respuesta_ya_registrado(email):
    return {
        "resultado": "ya_registrado",
        "notificacion": notificacion(
            "info", "Ya estás registrado",
            "Este correo ya tiene una cuenta en SG-CICT. Te llevamos al inicio de sesión."),
        "redirect": _redirect_login(email, "ya_registrado"),
    }


def _deshacer_solicitud(ref, resultado):
    try:
        if resultado == "creada":
            ref.delete()
        else:
            ref.update({"estado": K.ESTADO_RECHAZADA, "motivo_rechazo": "Error técnico al reabrir la solicitud"})
    except Exception:
        log.exception("No se pudo deshacer la solicitud")


# ───────────────────── Administración ─────────────────────
def listar_solicitudes(estado=K.ESTADO_PENDIENTE, limite=50):
    """Cola de revisión: primero investigadores UCO (prioridad 0), después externos; FIFO dentro de cada grupo."""
    if estado not in (K.ESTADO_PENDIENTE, K.ESTADO_APROBADA, K.ESTADO_RECHAZADA):
        raise RegistroError("estado_invalido", "Estado de solicitud no válido.", 422)
    consulta = (get_db().collection(K.COL_SOLICITUDES)
                .where(filter=FieldFilter("estado", "==", estado))
                .order_by("prioridad").order_by("creado_en")
                .limit(max(1, min(int(limite), 200))))
    return [_serializar(d) for d in consulta.stream()]


def aprobar_solicitud(solicitud_id, admin_uid, forzar=False, motivo_forzado=""):
    db = get_db()
    ref = db.collection(K.COL_SOLICITUDES).document(solicitud_id)
    snap = ref.get()
    if not snap.exists:
        raise RegistroError("no_encontrada", "La solicitud no existe.", 404)
    s = snap.to_dict()
    if s["estado"] != K.ESTADO_PENDIENTE:
        raise RegistroError("estado_invalido", f"La solicitud ya está {s['estado']}.", 409)

    # Regla de prioridad: no se aprueba un externo si quedan solicitudes UCO pendientes
    forzada = False
    if s["prioridad"] > K.PRIORIDAD_UCO:
        previas = (db.collection(K.COL_SOLICITUDES)
                   .where(filter=FieldFilter("estado", "==", K.ESTADO_PENDIENTE))
                   .where(filter=FieldFilter("prioridad", "<", s["prioridad"])).limit(1).get())
        if previas:
            if not (forzar and (motivo_forzado or "").strip()):
                raise RegistroError(
                    "prioridad_uco",
                    "Hay solicitudes de investigadores UCO pendientes. Atiéndelas antes o indica un motivo para saltar la prioridad.",
                    409)
            forzada = True

    uid = s.get("uid")
    if not uid:
        raise RegistroError("sin_cuenta", "La solicitud no tiene cuenta asociada.", 409)
    usuario_ref = db.collection(K.COL_USUARIOS).document(uid)
    perfil_ref = (db.collection(K.COL_PERFILES_UCO).document(s["perfil_uco_id"])
                  if s.get("perfil_uco_id") else None)

    @gcf.transactional
    def _tx(tx):
        actual = ref.get(transaction=tx).to_dict()
        if not actual or actual["estado"] != K.ESTADO_PENDIENTE:
            raise RegistroError("estado_invalido", "La solicitud ya fue revisada.", 409)
        perfil = {}
        if perfil_ref is not None:
            p = perfil_ref.get(transaction=tx)
            perfil = p.to_dict() if p.exists else {}
            if perfil.get("vinculado_a"):
                raise RegistroError("acreditacion_vinculada", "Esa acreditación ya está vinculada a otra cuenta.", 409)
        tx.set(usuario_ref, {
            "uid": uid, "email": s["email"], "nombre": s["nombre"], "apellidos": s["apellidos"],
            "tipo": s["tipo"], "prioridad": s["prioridad"], "rol": K.ROL_INVESTIGADOR,
            "estado": K.USUARIO_ACTIVO, "acreditacion": s.get("acreditacion"),
            "perfil_uco_id": s.get("perfil_uco_id"),
            "institucion": s["institucion"],
            "departamento": perfil.get("departamento"), "centro": perfil.get("centro"),
            "creado_en": gcf.SERVER_TIMESTAMP, "solicitud_id": solicitud_id,
        })
        tx.update(ref, {
            "estado": K.ESTADO_APROBADA, "revisado_por": admin_uid,
            "revisado_en": gcf.SERVER_TIMESTAMP, "prioridad_saltada": forzada,
            "motivo_prioridad_saltada": motivo_forzado.strip() if forzada else None,
        })
        if perfil_ref is not None:
            tx.update(perfil_ref, {"vinculado_a": uid})

    _tx(db.transaction())

    try:
        fb_auth.update_user(uid, disabled=False)
        fb_auth.set_custom_user_claims(uid, {"rol": K.ROL_INVESTIGADOR, "tipo": s["tipo"]})
    except Exception:
        log.exception("No se pudo activar la cuenta; revirtiendo la aprobación")
        usuario_ref.delete()
        ref.update({"estado": K.ESTADO_PENDIENTE, "revisado_por": None, "revisado_en": None})
        if perfil_ref is not None:
            perfil_ref.update({"vinculado_a": None})
        raise RegistroError("error_auth", "No se pudo activar la cuenta. La solicitud sigue pendiente.", 502)

    _auditar("solicitud_aprobada", solicitud_id=solicitud_id, admin=admin_uid, prioridad_saltada=forzada)
    return {"resultado": "aprobada",
            "notificacion": notificacion("exito", "Solicitud aprobada", f"{s['email']} ya puede iniciar sesión.")}


def rechazar_solicitud(solicitud_id, admin_uid, motivo):
    motivo = (motivo or "").strip()
    if len(motivo) < 5:
        raise RegistroError("motivo_requerido", "Indica el motivo del rechazo (mínimo 5 caracteres).", 422)
    db = get_db()
    ref = db.collection(K.COL_SOLICITUDES).document(solicitud_id)

    @gcf.transactional
    def _tx(tx):
        snap = ref.get(transaction=tx)
        if not snap.exists:
            raise RegistroError("no_encontrada", "La solicitud no existe.", 404)
        if snap.to_dict()["estado"] != K.ESTADO_PENDIENTE:
            raise RegistroError("estado_invalido", "La solicitud ya fue revisada.", 409)
        tx.update(ref, {"estado": K.ESTADO_RECHAZADA, "motivo_rechazo": motivo,
                        "revisado_por": admin_uid, "revisado_en": gcf.SERVER_TIMESTAMP})

    _tx(db.transaction())
    _auditar("solicitud_rechazada", solicitud_id=solicitud_id, admin=admin_uid)
    return {"resultado": "rechazada",
            "notificacion": notificacion("info", "Solicitud rechazada", "Se guardó el motivo del rechazo.")}
