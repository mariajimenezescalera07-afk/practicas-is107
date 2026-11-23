"""
HU2. Consulta del catálogo de equipos y laboratorios.

COMO investigador, QUIERO consultar el catálogo de equipos y laboratorios disponibles,
PARA conocer los recursos de investigación existentes y elegir los más adecuados.

Criterios de validación:
  1. El investigador puede acceder al catálogo de equipos y laboratorios.
  2. El sistema muestra todos los equipos y laboratorios registrados.
  3. El investigador puede consultar la información detallada de cada recurso.
  4. La información incluye nombre, descripción, ubicación, responsable y disponibilidad.
  5. El catálogo puede consultarse de forma clara y organizada.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class TipoRecurso(Enum):
    EQUIPO = "Equipo"
    LABORATORIO = "Laboratorio"


@dataclass
class Recurso:
    codigo: str
    tipo: TipoRecurso
    nombre: str
    descripcion: str
    ubicacion: str
    responsable: str
    disponible: bool = True

    def informacion(self) -> dict[str, str]:
        """Devuelve los campos que debe mostrar la ficha del recurso."""
        return {
            "codigo": self.codigo,
            "tipo": self.tipo.value,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "ubicacion": self.ubicacion,
            "responsable": self.responsable,
            "disponibilidad": "Disponible" if self.disponible else "No disponible",
        }


class Catalogo:
    """Registro consultable de equipos y laboratorios."""

    def __init__(self):
        self._recursos: dict[str, Recurso] = {}

    def anadir_recurso(self, recurso: Recurso) -> None:
        self._recursos[recurso.codigo] = recurso

    # Criterios 1 y 2: consultar todos los recursos registrados
    def listar_recursos(self) -> list[Recurso]:
        return sorted(self._recursos.values(), key=lambda r: (r.tipo.value, r.nombre.lower()))

    # Criterios 3 y 4: mostrar la información detallada de un recurso
    def obtener_recurso(self, codigo: str) -> Recurso:
        if codigo not in self._recursos:
            raise KeyError(f"No existe el recurso {codigo}")
        return self._recursos[codigo]

    # Criterio 5: resumen legible y ordenado de equipos y laboratorios
    def listar_con_disponibilidad(self) -> list[tuple[str, str, str, str]]:
        return [
            (recurso.codigo, recurso.tipo.value, recurso.nombre, recurso.informacion()["disponibilidad"])
            for recurso in self.listar_recursos()
        ]
    