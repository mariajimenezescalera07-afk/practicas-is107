from solicitudes import (
    Investigador,
    Administrador,
    SistemaSolicitudes
)

sistema = SistemaSolicitudes()

administrador = Administrador(
    "Administrador1"
)

investigador = Investigador(
    "Investigador1",
    "investigador1@correo.com"
)

solicitud = sistema.crear_solicitud(
    investigador
)

print("Solicitudes pendientes:")
print(
    len(
        sistema.obtener_solicitudes_pendientes()
    )
)

sistema.aprobar_solicitud(
    solicitud
)

print("Estado:", solicitud.estado)

print(
    "Usuario validado:",
    investigador.validado
)
