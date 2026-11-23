"""Pruebas de los endpoints HTTP (cliente de pruebas de Flask)."""
import unittest

import support  # noqa: F401  (debe ir antes que el código de src)
from support import AUTH, DB, BaseTest, crear_perfil_uco, crear_usuario, payload, payload_uco

import constants as K
from services import registro as svc

CLIENTE = None


def setUpModule():
    global CLIENTE
    from app import create_app
    CLIENTE = create_app().test_client()


def cab(uid):
    return {"Authorization": f"Bearer tok:{uid}"}


class RegistroApiTest(BaseTest):
    def test_health(self):
        r = CLIENTE.get("/api/health")
        self.assertEqual((r.status_code, r.get_json()), (200, {"ok": True}))

    def test_registro_nuevo_devuelve_201(self):
        r = CLIENTE.post("/api/registro", json=payload())
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["resultado"], "solicitud_creada")

    def test_usuario_ya_registrado_devuelve_409_con_aviso_y_redireccion(self):
        crear_usuario("u1", "carla@ejemplo.org")
        r = CLIENTE.post("/api/registro", json=payload())
        cuerpo = r.get_json()
        self.assertEqual(r.status_code, 409)
        self.assertEqual(cuerpo["notificacion"]["tipo"], "info")
        self.assertIn("/login.html", cuerpo["redirect"]["url"])

    def test_validacion_devuelve_422_con_detalles_y_notificacion_de_error(self):
        r = CLIENTE.post("/api/registro", json=payload(email="mal"))
        cuerpo = r.get_json()
        self.assertEqual(r.status_code, 422)
        self.assertIn("email", cuerpo["error"]["detalles"])
        self.assertEqual(cuerpo["notificacion"]["tipo"], "error")

    def test_cuerpo_que_no_es_json_devuelve_400(self):
        r = CLIENTE.post("/api/registro", data="no soy json", content_type="text/plain")
        self.assertEqual(r.status_code, 400)

    def test_config_web_expone_solo_las_claves_publicas(self):
        cuerpo = CLIENTE.get("/api/config/firebase-web").get_json()
        self.assertEqual(set(cuerpo), {"apiKey", "authDomain", "projectId", "appId"})

    def test_la_raiz_sirve_el_formulario_de_registro(self):
        r = CLIENTE.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Solicita tu acceso", r.get_data(as_text=True))
        r.close()


class AdministracionApiTest(BaseTest):
    def setUp(self):
        super().setUp()
        crear_usuario("adm1", "admin@uco.es", rol=K.ROL_ADMIN)
        crear_usuario("inv1", "inv@uco.es", rol=K.ROL_INVESTIGADOR)

    def test_sin_token_401(self):
        self.assertEqual(CLIENTE.get("/api/admin/solicitudes").status_code, 401)

    def test_token_invalido_401(self):
        r = CLIENTE.get("/api/admin/solicitudes", headers={"Authorization": "Bearer basura"})
        self.assertEqual(r.status_code, 401)

    def test_investigador_sin_rol_admin_recibe_403(self):
        self.assertEqual(CLIENTE.get("/api/admin/solicitudes", headers=cab("inv1")).status_code, 403)

    def test_admin_suspendido_recibe_403(self):
        crear_usuario("adm2", "otro@uco.es", rol=K.ROL_ADMIN, estado=K.USUARIO_SUSPENDIDO)
        self.assertEqual(CLIENTE.get("/api/admin/solicitudes", headers=cab("adm2")).status_code, 403)

    def test_admin_lista_la_cola_con_los_uco_primero(self):
        crear_perfil_uco()
        svc.registrar_investigador(payload())
        svc.registrar_investigador(payload_uco())
        r = CLIENTE.get("/api/admin/solicitudes", headers=cab("adm1"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual([s["email"] for s in r.get_json()["solicitudes"]],
                         ["ana.ruiz@uco.es", "carla@ejemplo.org"])

    def test_admin_aprueba_una_solicitud(self):
        svc.registrar_investigador(payload())
        sid = svc.id_solicitud("carla@ejemplo.org")
        r = CLIENTE.post(f"/api/admin/solicitudes/{sid}/aprobar", headers=cab("adm1"), json={})
        self.assertEqual((r.status_code, r.get_json()["resultado"]), (200, "aprobada"))
        self.assertFalse(AUTH.users["carla@ejemplo.org"].disabled)

    def test_aprobar_un_externo_con_uco_pendientes_devuelve_409_prioridad_uco(self):
        crear_perfil_uco()
        svc.registrar_investigador(payload())
        svc.registrar_investigador(payload_uco())
        sid = svc.id_solicitud("carla@ejemplo.org")
        r = CLIENTE.post(f"/api/admin/solicitudes/{sid}/aprobar", headers=cab("adm1"), json={})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.get_json()["error"]["codigo"], "prioridad_uco")
        r = CLIENTE.post(f"/api/admin/solicitudes/{sid}/aprobar", headers=cab("adm1"),
                         json={"forzar": True, "motivo": "Convenio urgente"})
        self.assertEqual(r.status_code, 200)

    def test_admin_rechaza_con_motivo_y_sin_motivo_falla(self):
        svc.registrar_investigador(payload())
        sid = svc.id_solicitud("carla@ejemplo.org")
        r = CLIENTE.post(f"/api/admin/solicitudes/{sid}/rechazar", headers=cab("adm1"), json={})
        self.assertEqual(r.status_code, 422)
        r = CLIENTE.post(f"/api/admin/solicitudes/{sid}/rechazar", headers=cab("adm1"),
                         json={"motivo": "No acredita vinculación"})
        self.assertEqual((r.status_code, r.get_json()["resultado"]), (200, "rechazada"))
        self.assertEqual(DB.data[K.COL_SOLICITUDES][sid]["estado"], K.ESTADO_RECHAZADA)


if __name__ == "__main__":
    unittest.main()
