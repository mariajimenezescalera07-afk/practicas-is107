"""Soporte para los tests: sustituye Firebase por una versión en memoria.

Se importa SIEMPRE antes que el código de src/backend. Así los tests no tocan
nunca un proyecto real de Firebase y se pueden ejecutar sin red ni credenciales.
"""
import copy
import os
import sys
import types
import unittest
from datetime import datetime, timedelta

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(RAIZ, "src", "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

SERVER_TIMESTAMP = object()


# ───────────────────────── Firestore en memoria ─────────────────────────
class FieldFilter:
    def __init__(self, field_path, op_string, value):
        self.campo, self.op, self.valor = field_path, op_string, value


def _cumple(doc, f):
    actual = doc.get(f.campo)
    if f.op == "==":
        return actual == f.valor
    if f.op == "<":
        return actual is not None and actual < f.valor
    raise NotImplementedError(f.op)


class Snap:
    def __init__(self, id_, datos):
        self.id, self._datos = id_, datos

    @property
    def exists(self):
        return self._datos is not None

    def to_dict(self):
        return None if self._datos is None else copy.deepcopy(self._datos)


class Query:
    def __init__(self, db, col, filtros=(), orden=(), limite=None):
        self.db, self.col, self.filtros, self.orden, self.limite = db, col, filtros, orden, limite

    def where(self, *args, filter=None):
        return Query(self.db, self.col, self.filtros + (filter,), self.orden, self.limite)

    def order_by(self, campo):
        return Query(self.db, self.col, self.filtros, self.orden + (campo,), self.limite)

    def limit(self, n):
        return Query(self.db, self.col, self.filtros, self.orden, n)

    def _ejecutar(self):
        filas = [(i, d) for i, d in self.db.data.get(self.col, {}).items()
                 if all(_cumple(d, f) for f in self.filtros)]
        for campo in reversed(self.orden):  # orden estable multi-campo
            filas.sort(key=lambda t: t[1].get(campo))
        if self.limite is not None:
            filas = filas[: self.limite]
        return [Snap(i, d) for i, d in filas]

    def get(self):
        return self._ejecutar()

    def stream(self):
        return iter(self._ejecutar())


class DocRef:
    def __init__(self, db, col, id_):
        self.db, self.col, self.id = db, col, id_

    def get(self, transaction=None):
        return Snap(self.id, self.db.data.get(self.col, {}).get(self.id))

    def set(self, datos, merge=False):
        col = self.db.data.setdefault(self.col, {})
        datos = self.db.resolver(datos)
        if merge and self.id in col:
            col[self.id].update(datos)
        else:
            col[self.id] = datos

    def update(self, datos):
        col = self.db.data.setdefault(self.col, {})
        if self.id not in col:
            raise KeyError(f"{self.col}/{self.id} no existe")
        col[self.id].update(self.db.resolver(datos))

    def delete(self):
        self.db.data.get(self.col, {}).pop(self.id, None)


class Collection(Query):
    def __init__(self, db, col):
        super().__init__(db, col)

    def document(self, id_):
        return DocRef(self.db, self.col, id_)

    def add(self, datos):
        id_ = f"auto{len(self.db.data.get(self.col, {})) + 1}"
        ref = self.document(id_)
        ref.set(datos)
        return None, ref


class Tx:
    def set(self, ref, datos):
        ref.set(datos)

    def update(self, ref, datos):
        ref.update(datos)


class FakeDB:
    def __init__(self):
        self.reset()

    def reset(self):
        self.data, self._tick = {}, 0

    def resolver(self, datos):
        salida = {}
        for k, v in datos.items():
            if v is SERVER_TIMESTAMP:
                self._tick += 1
                v = datetime(2026, 1, 1) + timedelta(seconds=self._tick)
            salida[k] = copy.deepcopy(v)
        return salida

    def collection(self, nombre):
        return Collection(self, nombre)

    def transaction(self):
        return Tx()


DB = FakeDB()


# ───────────────────────── Firebase Auth en memoria ─────────────────────────
class UserNotFoundError(Exception):
    pass


class UserRecord:
    def __init__(self, uid, email, password, display_name, disabled):
        self.uid, self.email, self.password = uid, email, password
        self.display_name, self.disabled = display_name, disabled


class AuthState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.users, self.claims = {}, {}


AUTH = AuthState()


def _get_user_by_email(email):
    if email not in AUTH.users:
        raise UserNotFoundError(email)
    return AUTH.users[email]


def _create_user(email, password=None, display_name=None, disabled=False):
    u = UserRecord(f"uid{len(AUTH.users) + 1}", email, password, display_name, disabled)
    AUTH.users[email] = u
    return u


def _update_user(uid, **cambios):
    u = next(x for x in AUTH.users.values() if x.uid == uid)
    for k in ("password", "display_name", "disabled"):
        if k in cambios:
            setattr(u, k, cambios[k])
    return u


def _set_custom_user_claims(uid, claims):
    AUTH.claims[uid] = claims


def _verify_id_token(token, check_revoked=False):
    if token.startswith("tok:"):
        return {"uid": token[4:]}
    raise ValueError("token no válido")


# ───────────────────────── Instalación de los módulos falsos ─────────────────────────
def _modulo(nombre, **atributos):
    m = types.ModuleType(nombre)
    m.__path__ = []
    m.__dict__.update(atributos)
    sys.modules[nombre] = m
    return m


def _instalar():
    base_query = _modulo("google.cloud.firestore_v1.base_query", FieldFilter=FieldFilter)
    v1 = _modulo("google.cloud.firestore_v1", base_query=base_query)
    gcf = _modulo("google.cloud.firestore", SERVER_TIMESTAMP=SERVER_TIMESTAMP,
                  transactional=lambda f: f)
    cloud = _modulo("google.cloud", firestore=gcf, firestore_v1=v1)
    _modulo("google", cloud=cloud)

    fa_auth = _modulo(
        "firebase_admin.auth", UserNotFoundError=UserNotFoundError,
        get_user_by_email=_get_user_by_email, create_user=_create_user,
        update_user=_update_user, set_custom_user_claims=_set_custom_user_claims,
        verify_id_token=_verify_id_token)
    fa_cred = _modulo("firebase_admin.credentials",
                      Certificate=lambda ruta: object(), ApplicationDefault=lambda: object())
    fa_fs = _modulo("firebase_admin.firestore", client=lambda: DB)
    fa = _modulo("firebase_admin", _apps={}, auth=fa_auth, credentials=fa_cred, firestore=fa_fs)
    fa.initialize_app = lambda cred=None, options=None: fa._apps.setdefault("[DEFAULT]", object())

    # Extensiones de Flask: solo se sustituyen si no están instaladas
    try:
        import flask_cors  # noqa: F401
    except ImportError:
        _modulo("flask_cors", CORS=lambda app, **kw: app)
    try:
        import flask_limiter  # noqa: F401
        import flask_limiter.util  # noqa: F401
    except ImportError:
        class Limiter:
            def __init__(self, *a, **kw):
                pass

            def limit(self, *a, **kw):
                return lambda f: f

        util = _modulo("flask_limiter.util", get_remote_address=lambda: "127.0.0.1")
        _modulo("flask_limiter", Limiter=Limiter, util=util)


_instalar()


# ───────────────────────── utilidades para los tests ─────────────────────────
class BaseTest(unittest.TestCase):
    def setUp(self):
        DB.reset()
        AUTH.reset()


def payload(**cambios):
    """Solicitud de un investigador externo válido."""
    datos = {"nombre": "Carla", "apellidos": "Gómez Ruiz", "email": "carla@ejemplo.org",
             "password": "contraseña-larga-1", "es_uco": False, "acreditacion": "",
             "institucion": "CSIC", "acepta_tratamiento": True}
    datos.update(cambios)
    return datos


def payload_uco(**cambios):
    """Solicitud de un investigador que declara ser de la UCO."""
    datos = payload(nombre="Ana", apellidos="Ruiz Molina", email="ana.ruiz@uco.es",
                    es_uco=True, acreditacion="UCO-0001", institucion="")
    datos.update(cambios)
    return datos


def crear_perfil_uco(acreditacion="UCO-0001", email="ana.ruiz@uco.es", activo=True, vinculado_a=None):
    DB.data.setdefault("perfiles_uco", {})[acreditacion] = {
        "acreditacion": acreditacion, "nombre": "Ana Ruiz Molina", "email_institucional": email,
        "departamento": "Química Orgánica", "centro": "Facultad de Ciencias",
        "activo": activo, "vinculado_a": vinculado_a}


def crear_usuario(uid, email, rol="investigador", estado="activo"):
    DB.data.setdefault("usuarios", {})[uid] = {
        "uid": uid, "email": email, "rol": rol, "estado": estado}
