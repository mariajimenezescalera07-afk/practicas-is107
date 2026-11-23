"""Pruebas de la lógica de negocio de la HU1 (registro con acreditación)."""
import unittest

import support  # noqa: F401  (debe ir antes que el código de src)
from support import AUTH, DB, BaseTest, crear_perfil_uco, crear_usuario, payload, payload_uco

import constants as K
from services import registro as svc


def solicitud_de(email):
    return DB.data[K.COL_SOLICITUDES][svc.id_solicitud(email)]


class ValidacionTest(BaseTest):
    def test_campos_invalidos_devuelven_422_con_detalle_por_campo(self):
        malo = payload(nombre="", apellidos="", email="no-es-correo", password="corta",
                       acepta_tratamiento=False)
        with self.assertRaises(svc.RegistroError) as cm:
            svc.registrar_investigador(malo)
        self.assertEqual(cm.exception.status, 422)
        self.assertEqual(set(cm.exception.detalles),
                         {"nombre", "apellidos", "email", "password", "acepta_tratamiento"})

    def test_uco_exige_acreditacion_con_formato_valido(self):
        with self.assertRaises(svc.RegistroError) as cm:
            svc.registrar_investigador(payload_uco(acreditacion="a b"))
        self.assertIn("acreditacion", cm.exception.detalles)

    def test_externo_exige_institucion(self):
        with self.assertRaises(svc.RegistroError) as cm:
            svc.registrar_investigador(payload(institucion=""))
        self.assertIn("institucion", cm.exception.detalles)

    def test_cuerpo_que_no_es_objeto_se_rechaza(self):
        with self.assertRaises(svc.RegistroError) as cm:
            svc.registrar_investigador(None)
        self.assertEqual(cm.exception.status, 400)

    def test_no_se_crea_nada_si_la_validacion_falla(self):
        with self.assertRaises(svc.RegistroError):
            svc.registrar_investigador(payload(email="x"))
        self.assertEqual(DB.data, {})
        self.assertEqual(AUTH.users, {})


class UsuarioNuevoTest(BaseTest):
    def test_externo_crea_solicitud_pendiente_con_prioridad_baja(self):
        cuerpo, status = svc.registrar_investigador(payload())
        self.assertEqual(status, 201)
        self.assertEqual(cuerpo["resultado"], "solicitud_creada")
        self.assertEqual(cuerpo["notificacion"]["tipo"], "exito")
        sol = solicitud_de("carla@ejemplo.org")
        self.assertEqual(sol["estado"], K.ESTADO_PENDIENTE)
        self.assertEqual(sol["tipo"], K.TIPO_EXTERNO)
        self.assertEqual(sol["prioridad"], K.PRIORIDAD_EXTERNO)

    def test_la_cuenta_de_auth_se_crea_deshabilitada_y_ligada_a_la_solicitud(self):
        svc.registrar_investigador(payload())
        cuenta = AUTH.users["carla@ejemplo.org"]
        self.assertTrue(cuenta.disabled)
        self.assertEqual(solicitud_de("carla@ejemplo.org")["uid"], cuenta.uid)

    def test_la_contrasena_nunca_se_guarda_en_firestore(self):
        svc.registrar_investigador(payload(password="contraseña-secreta-9"))
        self.assertNotIn("contraseña-secreta-9", str(DB.data))

    def test_no_se_crea_ficha_de_usuario_hasta_la_aprobacion(self):
        svc.registrar_investigador(payload())
        self.assertNotIn(K.COL_USUARIOS, DB.data)

    def test_el_email_se_normaliza(self):
        svc.registrar_investigador(payload(email="  CARLA@Ejemplo.ORG "))
        self.assertIn("carla@ejemplo.org", AUTH.users)
        self.assertEqual(solicitud_de("carla@ejemplo.org")["email"], "carla@ejemplo.org")


class PrioridadUCOTest(BaseTest):
    def test_uco_con_acreditacion_verificada_tiene_prioridad_maxima(self):
        crear_perfil_uco()
        cuerpo, status = svc.registrar_investigador(payload_uco())
        self.assertEqual(status, 201)
        self.assertEqual(cuerpo["tipo"], K.TIPO_UCO)
        self.assertEqual(cuerpo["prioridad"], K.PRIORIDAD_UCO)
        self.assertEqual(cuerpo["verificacion_uco"], K.VERIF_VERIFICADA)
        self.assertEqual(solicitud_de("ana.ruiz@uco.es")["perfil_uco_id"], "UCO-0001")

    def test_acreditacion_inexistente_no_da_prioridad_y_pasa_a_revision_manual(self):
        cuerpo, _ = svc.registrar_investigador(payload_uco(acreditacion="UCO-9999"))
        self.assertEqual(cuerpo["tipo"], K.TIPO_EXTERNO)
        self.assertEqual(cuerpo["prioridad"], K.PRIORIDAD_EXTERNO)
        self.assertEqual(cuerpo["verificacion_uco"], K.VERIF_NO_ENCONTRADA)
        self.assertIn("manualmente", cuerpo["notificacion"]["mensaje"])
        self.assertEqual(solicitud_de("ana.ruiz@uco.es")["tipo_declarado"], K.TIPO_UCO)

    def test_correo_ajeno_a_la_uco_y_distinto_al_del_padron_no_verifica(self):
        crear_perfil_uco()
        cuerpo, _ = svc.registrar_investigador(payload_uco(email="ana@gmail.com"))
        self.assertEqual(cuerpo["verificacion_uco"], K.VERIF_EMAIL_NO_COINCIDE)
        self.assertEqual(cuerpo["prioridad"], K.PRIORIDAD_EXTERNO)

    def test_correo_igual_al_del_padron_verifica_aunque_no_sea_de_dominio_uco(self):
        crear_perfil_uco(email="ana@laboratorio-asociado.es")
        cuerpo, _ = svc.registrar_investigador(payload_uco(email="ana@laboratorio-asociado.es"))
        self.assertEqual(cuerpo["verificacion_uco"], K.VERIF_VERIFICADA)

    def test_perfil_inactivo_no_da_prioridad(self):
        crear_perfil_uco(activo=False)
        cuerpo, _ = svc.registrar_investigador(payload_uco())
        self.assertEqual(cuerpo["verificacion_uco"], K.VERIF_INACTIVA)
        self.assertEqual(cuerpo["prioridad"], K.PRIORIDAD_EXTERNO)

    def test_acreditacion_ya_vinculada_a_otra_cuenta_no_da_prioridad(self):
        crear_perfil_uco(vinculado_a="otro-uid")
        cuerpo, _ = svc.registrar_investigador(payload_uco())
        self.assertEqual(cuerpo["verificacion_uco"], K.VERIF_YA_VINCULADA)
        self.assertEqual(cuerpo["prioridad"], K.PRIORIDAD_EXTERNO)

    def test_el_cliente_no_puede_imponer_tipo_ni_prioridad(self):
        malicioso = payload(tipo="uco", prioridad=0, estado="aprobada")
        svc.registrar_investigador(malicioso)
        sol = solicitud_de("carla@ejemplo.org")
        self.assertEqual(sol["prioridad"], K.PRIORIDAD_EXTERNO)
        self.assertEqual(sol["tipo"], K.TIPO_EXTERNO)
        self.assertEqual(sol["estado"], K.ESTADO_PENDIENTE)


class UsuarioYaRegistradoTest(BaseTest):
    def test_devuelve_409_aviso_informativo_y_redireccion_al_login(self):
        crear_usuario("u1", "carla@ejemplo.org")
        cuerpo, status = svc.registrar_investigador(payload())
        self.assertEqual(status, 409)
        self.assertEqual(cuerpo["resultado"], "ya_registrado")
        self.assertEqual(cuerpo["notificacion"]["tipo"], "info")
        url = cuerpo["redirect"]["url"]
        self.assertTrue(url.startswith("/login.html?"))
        self.assertIn("aviso=ya_registrado", url)
        self.assertIn("carla%40ejemplo.org", url)
        self.assertGreater(cuerpo["redirect"]["espera_ms"], 0)

    def test_no_crea_solicitud_ni_cuenta_de_auth(self):
        crear_usuario("u1", "carla@ejemplo.org")
        svc.registrar_investigador(payload())
        self.assertNotIn(K.COL_SOLICITUDES, DB.data)
        self.assertEqual(AUTH.users, {})

    def test_detecta_al_usuario_aunque_cambien_mayusculas_y_espacios(self):
        crear_usuario("u1", "carla@ejemplo.org")
        _, status = svc.registrar_investigador(payload(email=" Carla@EJEMPLO.org "))
        self.assertEqual(status, 409)

    def test_usuario_suspendido_tambien_cuenta_como_registrado(self):
        crear_usuario("u1", "carla@ejemplo.org", estado=K.USUARIO_SUSPENDIDO)
        _, status = svc.registrar_investigador(payload())
        self.assertEqual(status, 409)

    def test_tras_ser_aprobado_un_nuevo_intento_redirige_al_login(self):
        svc.registrar_investigador(payload())
        svc.aprobar_solicitud(svc.id_solicitud("carla@ejemplo.org"), "admin1")
        cuerpo, status = svc.registrar_investigador(payload())
        self.assertEqual((status, cuerpo["resultado"]), (409, "ya_registrado"))


class SolicitudExistenteTest(BaseTest):
    def test_solicitud_pendiente_no_se_duplica_ni_cambia_la_contrasena(self):
        svc.registrar_investigador(payload(password="primera-contraseña-1"))
        cuerpo, status = svc.registrar_investigador(payload(password="otra-contraseña-distinta"))
        self.assertEqual(status, 200)
        self.assertEqual(cuerpo["resultado"], "solicitud_en_curso")
        self.assertEqual(cuerpo["notificacion"]["tipo"], "aviso")
        self.assertEqual(len(DB.data[K.COL_SOLICITUDES]), 1)
        self.assertEqual(AUTH.users["carla@ejemplo.org"].password, "primera-contraseña-1")

    def test_solicitud_rechazada_puede_reenviarse(self):
        svc.registrar_investigador(payload())
        svc.rechazar_solicitud(svc.id_solicitud("carla@ejemplo.org"), "admin1", "Datos incompletos")
        cuerpo, status = svc.registrar_investigador(payload(institucion="Otra institución"))
        self.assertEqual(status, 201)
        sol = solicitud_de("carla@ejemplo.org")
        self.assertEqual(sol["estado"], K.ESTADO_PENDIENTE)
        self.assertEqual(sol["intentos"], 2)
        self.assertEqual(sol["institucion"], "Otra institución")
        self.assertIsNone(sol["motivo_rechazo"])

    def test_cuenta_de_auth_activa_sin_ficha_no_se_toca_y_se_deshace_la_solicitud(self):
        AUTH.users["carla@ejemplo.org"] = support.UserRecord(
            "uid-ajeno", "carla@ejemplo.org", "clave-original", "Otra persona", False)
        with self.assertRaises(svc.RegistroError) as cm:
            svc.registrar_investigador(payload(password="clave-del-atacante"))
        self.assertEqual((cm.exception.codigo, cm.exception.status), ("cuenta_existente", 409))
        cuenta = AUTH.users["carla@ejemplo.org"]
        self.assertEqual(cuenta.password, "clave-original")
        self.assertFalse(cuenta.disabled)
        self.assertEqual(DB.data.get(K.COL_SOLICITUDES, {}), {})


class AprobacionTest(BaseTest):
    def test_aprobar_crea_el_usuario_activa_la_cuenta_y_vincula_la_acreditacion(self):
        crear_perfil_uco()
        svc.registrar_investigador(payload_uco())
        sid = svc.id_solicitud("ana.ruiz@uco.es")
        uid = solicitud_de("ana.ruiz@uco.es")["uid"]

        res = svc.aprobar_solicitud(sid, "admin1")

        self.assertEqual(res["resultado"], "aprobada")
        usuario = DB.data[K.COL_USUARIOS][uid]
        self.assertEqual(usuario["rol"], K.ROL_INVESTIGADOR)
        self.assertEqual(usuario["tipo"], K.TIPO_UCO)
        self.assertEqual(usuario["prioridad"], K.PRIORIDAD_UCO)
        self.assertEqual(usuario["departamento"], "Química Orgánica")
        self.assertFalse(AUTH.users["ana.ruiz@uco.es"].disabled)
        self.assertEqual(AUTH.claims[uid]["tipo"], K.TIPO_UCO)
        self.assertEqual(solicitud_de("ana.ruiz@uco.es")["estado"], K.ESTADO_APROBADA)
        self.assertEqual(solicitud_de("ana.ruiz@uco.es")["revisado_por"], "admin1")
        self.assertEqual(DB.data[K.COL_PERFILES_UCO]["UCO-0001"]["vinculado_a"], uid)

    def test_no_se_puede_aprobar_dos_veces(self):
        svc.registrar_investigador(payload())
        sid = svc.id_solicitud("carla@ejemplo.org")
        svc.aprobar_solicitud(sid, "admin1")
        with self.assertRaises(svc.RegistroError) as cm:
            svc.aprobar_solicitud(sid, "admin1")
        self.assertEqual((cm.exception.codigo, cm.exception.status), ("estado_invalido", 409))

    def test_solicitud_inexistente_devuelve_404(self):
        with self.assertRaises(svc.RegistroError) as cm:
            svc.aprobar_solicitud("no-existe", "admin1")
        self.assertEqual(cm.exception.status, 404)


class PrioridadEnLaAprobacionTest(BaseTest):
    def setUp(self):
        super().setUp()
        crear_perfil_uco()
        svc.registrar_investigador(payload())          # externo llega primero
        svc.registrar_investigador(payload_uco())      # UCO llega después
        self.id_ext = svc.id_solicitud("carla@ejemplo.org")
        self.id_uco = svc.id_solicitud("ana.ruiz@uco.es")

    def test_no_se_aprueba_a_un_externo_mientras_haya_uco_pendientes(self):
        with self.assertRaises(svc.RegistroError) as cm:
            svc.aprobar_solicitud(self.id_ext, "admin1")
        self.assertEqual((cm.exception.codigo, cm.exception.status), ("prioridad_uco", 409))
        self.assertEqual(DB.data[K.COL_SOLICITUDES][self.id_ext]["estado"], K.ESTADO_PENDIENTE)

    def test_forzar_sin_motivo_sigue_bloqueado(self):
        with self.assertRaises(svc.RegistroError) as cm:
            svc.aprobar_solicitud(self.id_ext, "admin1", forzar=True, motivo_forzado="  ")
        self.assertEqual(cm.exception.codigo, "prioridad_uco")

    def test_forzar_con_motivo_permite_saltar_la_prioridad_y_lo_deja_registrado(self):
        svc.aprobar_solicitud(self.id_ext, "admin1", forzar=True, motivo_forzado="Convenio urgente")
        sol = DB.data[K.COL_SOLICITUDES][self.id_ext]
        self.assertEqual(sol["estado"], K.ESTADO_APROBADA)
        self.assertTrue(sol["prioridad_saltada"])
        self.assertEqual(sol["motivo_prioridad_saltada"], "Convenio urgente")

    def test_un_uco_se_aprueba_aunque_haya_externos_pendientes(self):
        svc.aprobar_solicitud(self.id_uco, "admin1")
        self.assertEqual(DB.data[K.COL_SOLICITUDES][self.id_uco]["estado"], K.ESTADO_APROBADA)

    def test_el_externo_se_aprueba_sin_forzar_cuando_ya_no_quedan_uco(self):
        svc.aprobar_solicitud(self.id_uco, "admin1")
        svc.aprobar_solicitud(self.id_ext, "admin1")
        sol = DB.data[K.COL_SOLICITUDES][self.id_ext]
        self.assertEqual(sol["estado"], K.ESTADO_APROBADA)
        self.assertFalse(sol["prioridad_saltada"])


class ColaDeRevisionTest(BaseTest):
    def test_la_cola_muestra_primero_a_los_uco_y_despues_fifo_entre_externos(self):
        crear_perfil_uco()
        svc.registrar_investigador(payload(email="ext1@ejemplo.org"))
        svc.registrar_investigador(payload(email="ext2@ejemplo.org"))
        svc.registrar_investigador(payload_uco())
        orden = [s["email"] for s in svc.listar_solicitudes()]
        self.assertEqual(orden, ["ana.ruiz@uco.es", "ext1@ejemplo.org", "ext2@ejemplo.org"])

    def test_el_listado_serializa_las_fechas_y_no_incluye_contrasenas(self):
        svc.registrar_investigador(payload())
        fila = svc.listar_solicitudes()[0]
        self.assertIsInstance(fila["creado_en"], str)
        self.assertNotIn("password", fila)

    def test_filtra_por_estado(self):
        svc.registrar_investigador(payload())
        self.assertEqual(svc.listar_solicitudes(K.ESTADO_APROBADA), [])
        self.assertEqual(len(svc.listar_solicitudes(K.ESTADO_PENDIENTE)), 1)

    def test_estado_desconocido_devuelve_422(self):
        with self.assertRaises(svc.RegistroError) as cm:
            svc.listar_solicitudes("inventado")
        self.assertEqual(cm.exception.status, 422)


class RechazoTest(BaseTest):
    def test_rechazar_guarda_motivo_y_mantiene_la_cuenta_deshabilitada(self):
        svc.registrar_investigador(payload())
        sid = svc.id_solicitud("carla@ejemplo.org")
        svc.rechazar_solicitud(sid, "admin1", "No acredita vinculación")
        sol = DB.data[K.COL_SOLICITUDES][sid]
        self.assertEqual(sol["estado"], K.ESTADO_RECHAZADA)
        self.assertEqual(sol["motivo_rechazo"], "No acredita vinculación")
        self.assertEqual(sol["revisado_por"], "admin1")
        self.assertTrue(AUTH.users["carla@ejemplo.org"].disabled)
        self.assertNotIn(K.COL_USUARIOS, DB.data)

    def test_el_motivo_es_obligatorio(self):
        svc.registrar_investigador(payload())
        with self.assertRaises(svc.RegistroError) as cm:
            svc.rechazar_solicitud(svc.id_solicitud("carla@ejemplo.org"), "admin1", " no ")
        self.assertEqual((cm.exception.codigo, cm.exception.status), ("motivo_requerido", 422))

    def test_no_se_puede_rechazar_una_solicitud_ya_aprobada(self):
        svc.registrar_investigador(payload())
        sid = svc.id_solicitud("carla@ejemplo.org")
        svc.aprobar_solicitud(sid, "admin1")
        with self.assertRaises(svc.RegistroError) as cm:
            svc.rechazar_solicitud(sid, "admin1", "Motivo suficiente")
        self.assertEqual(cm.exception.status, 409)


if __name__ == "__main__":
    unittest.main()
