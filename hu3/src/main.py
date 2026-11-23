"""Pequeña demo por consola de la HU3: consulta de disponibilidad de los equipos."""

from datetime import datetime, timedelta

from equipos import Catalogo, Equipo, ReservaError, Usuario


def mostrar_catalogo(catalogo: Catalogo, momento: datetime) -> None:
    print(f"\nCatálogo de equipos ({momento:%d/%m/%Y %H:%M})")
    print("-" * 50)
    for codigo, nombre, estado in catalogo.listar_con_estado(momento):
        print(f"{codigo:<6} {nombre:<28} {estado.value}")


def main() -> None:
    catalogo = Catalogo()
    catalogo.anadir_equipo(Equipo("EQ01", "Microscopio electrónico"))
    catalogo.anadir_equipo(Equipo("EQ02", "Espectrómetro de masas"))
    catalogo.anadir_equipo(Equipo("EQ03", "Centrifugadora", fuera_de_servicio=True))
    catalogo.anadir_equipo(Equipo("EQ04", "Termociclador PCR"))

    ahora = datetime.now().replace(second=0, microsecond=0)
    investigadora = Usuario("Ana", registrado=True, validado=True)
    sin_validar = Usuario("Luis", registrado=True, validado=False)

    mostrar_catalogo(catalogo, ahora)

    print("\nAna reserva el EQ01 durante 2 horas...")
    catalogo.reservar(investigadora, "EQ01", ahora, ahora + timedelta(hours=2))
    mostrar_catalogo(catalogo, ahora)

    print("\nDisponibles ahora:", [e.nombre for e in catalogo.equipos_disponibles(ahora)])

    for usuario, codigo in [(investigadora, "EQ01"), (sin_validar, "EQ02"), (investigadora, "EQ03")]:
        try:
            catalogo.reservar(usuario, codigo, ahora + timedelta(hours=1), ahora + timedelta(hours=3))
        except ReservaError as error:
            print(f"Reserva rechazada ({usuario.nombre}, {codigo}): {error}")


if __name__ == "__main__":
    main()
