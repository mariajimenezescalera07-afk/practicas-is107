"""Pequeña demo por consola de la HU1: registro de investigadores UCO."""

from registro_uco import (
    SistemaRegistro,
    Investigador,
    RegistroError
)


def mostrar_solicitudes(sistema: SistemaRegistro) -> None:
    print("\nSolicitudes registradas")
    print("-" * 40)

    for solicitud in sistema.solicitudes:
        print(
            f"{solicitud.investigador.nombre:<20} "
            f"{solicitud.investigador.acreditacion:<10} "
            f"{solicitud.estado.value}"
        )


def main() -> None:
    sistema = SistemaRegistro()

    investigadora_1 = Investigador(
        "Ana López",
        "UCO001"
    )

    investigadora_2 = Investigador(
        "María Pérez",
        "UCO002"
    )

    print("=== REGISTRO DE INVESTIGADORES UCO ===")

    print("\nPrimer registro:")
    print(
        sistema.registrar_usuario(
            investigadora_1
        )
    )

    print("\nSegundo registro:")
    print(
        sistema.registrar_usuario(
            investigadora_2
        )
    )

    print("\nIntentando registrar de nuevo a Ana:")
    print(
        sistema.registrar_usuario(
            investigadora_1
        )
    )

    mostrar_solicitudes(sistema)

    print("\nConsulta de una solicitud:")
    try:
        solicitud = sistema.obtener_solicitud("UCO001")

        print(
            f"Investigador: {solicitud.investigador.nombre}"
        )
        print(
            f"Estado: {solicitud.estado.value}"
        )
        print(
            f"Prioridad: {solicitud.investigador.prioridad}"
        )

    except RegistroError as error:
        print(error)


if __name__ == "__main__":
    main()