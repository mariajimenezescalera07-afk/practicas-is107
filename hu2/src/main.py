"""Pequeña demo por consola de la HU2: consulta del catálogo de recursos."""

from catalogo import Catalogo, Recurso, TipoRecurso


def mostrar_catalogo(catalogo: Catalogo) -> None:
    print("\nCatálogo de equipos y laboratorios")
    print("-" * 78)
    for codigo, tipo, nombre, disponibilidad in catalogo.listar_con_disponibilidad():
        print(f"{codigo:<7} {tipo:<13} {nombre:<35} {disponibilidad}")


def mostrar_detalle(catalogo: Catalogo, codigo: str) -> None:
    print(f"\nDetalle del recurso {codigo}")
    print("-" * 50)
    try:
        recurso = catalogo.obtener_recurso(codigo)
    except KeyError as error:
        print(error)
        return
    for campo, valor in recurso.informacion().items():
        print(f"{campo.capitalize():<16}: {valor}")


def main() -> None:
    catalogo = Catalogo()
    catalogo.anadir_recurso(Recurso(
        "EQ01", TipoRecurso.EQUIPO, "Microscopio óptico",
        "Observación de muestras biológicas", "Laboratorio de Biología",
        "Personal técnico", True,
    ))
    catalogo.anadir_recurso(Recurso(
        "EQ02", TipoRecurso.EQUIPO, "Centrífuga",
        "Separación de muestras", "Laboratorio de Química",
        "Personal técnico", False,
    ))
    catalogo.anadir_recurso(Recurso(
        "LAB01", TipoRecurso.LABORATORIO, "Laboratorio de análisis",
        "Espacio para análisis de muestras", "Edificio de investigación",
        "Coordinación de laboratorio", True,
    ))

    mostrar_catalogo(catalogo)
    mostrar_detalle(catalogo, "EQ01")
    mostrar_detalle(catalogo, "LAB01")


if __name__ == "__main__":
    main()
