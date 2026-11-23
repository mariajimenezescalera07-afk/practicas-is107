from incidencias import (
    Usuario,
    Equipo,
    SistemaIncidencias
)

sistema = SistemaIncidencias()

investigador = Usuario(
    "Investigador1",
    "investigador"
)

tecnico = Usuario(
    "Tecnico1",
    "tecnico"
)

equipo = Equipo(
    "Equipo1"
)

print("Registrando incidencia...")

sistema.registrar_incidencia(
    investigador,
    equipo,
    "El equipo no funciona correctamente"
)

print("Equipo averiado:", equipo.nombre)

print("\nListado de averiados:")

for equipo_averiado in sistema.obtener_equipos_averiados(
    tecnico
):
    print("-", equipo_averiado.nombre)

print("\nReparando equipo...")

sistema.reparar_equipo(equipo)

print(
    "Disponible:",
    equipo.disponible
)
