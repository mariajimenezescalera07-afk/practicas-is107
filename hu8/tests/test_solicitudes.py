from src.solicitudes import (
    Investigador,
    SistemaSolicitudes
)


def test_visualizar_solicitudes_pendientes():

    sistema = SistemaSolicitudes()

    investigador = Investigador(
        "Investigador1",
        "correo@uco.es"
    )

    sistema.crear_solicitud(
        investigador
    )

    assert len(
        sistema.obtener_solicitudes_pendientes()
    ) == 1


def test_aprobar_solicitud():

    sistema = SistemaSolicitudes()

    investigador = Investigador(
        "Investigador1",
        "correo@uco.es"
    )

    solicitud = sistema.crear_solicitud(
        investigador
    )

    sistema.aprobar_solicitud(
        solicitud
    )

    assert solicitud.estado == "APROBADA"


def test_rechazar_solicitud():

    sistema = SistemaSolicitudes()

    investigador = Investigador(
        "Investigador1",
        "correo@uco.es"
    )

    solicitud = sistema.crear_solicitud(
        investigador
    )

    sistema.rechazar_solicitud(
        solicitud
    )

    assert solicitud.estado == "RECHAZADA"


def test_usuario_aprobado_queda_validado():

    sistema = SistemaSolicitudes()

    investigador = Investigador(
        "Investigador1",
        "correo@uco.es"
    )

    solicitud = sistema.crear_solicitud(
        investigador
    )

    sistema.aprobar_solicitud(
        solicitud
    )

    assert investigador.validado


def test_usuario_rechazado_no_puede_reservar():

    sistema = SistemaSolicitudes()

    investigador = Investigador(
        "Investigador1",
        "correo@uco.es"
    )

    solicitud = sistema.crear_solicitud(
        investigador
    )

    sistema.rechazar_solicitud(
        solicitud
    )

    assert not sistema.puede_realizar_reserva(
        investigador
    )
