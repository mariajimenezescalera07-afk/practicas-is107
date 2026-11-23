"""
HU3. Consulta de disponibilidad de los equipos

COMO investigador, QUIERO ver qué equipos están disponibles en cada momento,
PARA saber cuáles puedo reservar.

Criterios de validación:
  1. El sistema tiene que mostrar los equipos disponibles.
  2. Se tiene que poder ver si un equipo está libre, reservado o no disponible.
  3. El estado del equipo tiene que actualizarse cuando se haga una reserva.
  4. No se debe poder reservar un equipo que ya esté reservado en ese tramo horario.
  5. El usuario tiene que estar registrado y validado para poder hacer una reserva.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EstadoEquipo(Enum):
    LIBRE = "Libre"
    RESERVADO = "Reservado"
    FUERA_DE_SERVICIO = "Fuera de servicio"


class ReservaError(Exception):
    """Error al intentar hacer una reserva."""


@dataclass
class Usuario:
    nombre: str
    registrado: bool = False
    validado: bool = False

    def puede_reservar(self) -> bool:
        return self.registrado and self.validado


@dataclass
class Reserva:
    usuario: Usuario
    inicio: datetime
    fin: datetime

    def solapa_con(self, inicio: datetime, fin: datetime) -> bool:
        # Dos tramos se solapan si uno empieza antes de que acabe el otro
        return self.inicio < fin and inicio < self.fin


@dataclass
class Equipo:
    codigo: str
    nombre: str
    fuera_de_servicio: bool = False
    reservas: list = field(default_factory=list)

    def esta_libre(self, inicio: datetime, fin: datetime) -> bool:
        if self.fuera_de_servicio:
            return False
        return not any(r.solapa_con(inicio, fin) for r in self.reservas)

    def estado(self, momento: datetime | None = None) -> EstadoEquipo:
        """Estado del equipo en un momento dado (por defecto, ahora)."""
        if self.fuera_de_servicio:
            return EstadoEquipo.FUERA_DE_SERVICIO
        momento = momento or datetime.now()
        for r in self.reservas:
            if r.inicio <= momento < r.fin:
                return EstadoEquipo.RESERVADO
        return EstadoEquipo.LIBRE


class Catalogo:
    """Catálogo de equipos que el investigador consulta desde la web."""

    def __init__(self):
        self._equipos: dict[str, Equipo] = {}

    def anadir_equipo(self, equipo: Equipo) -> None:
        self._equipos[equipo.codigo] = equipo

    def obtener_equipo(self, codigo: str) -> Equipo:
        if codigo not in self._equipos:
            raise KeyError(f"No existe el equipo {codigo}")
        return self._equipos[codigo]

    # Criterio 2: ver nombre y estado de cada equipo
    def listar_con_estado(self, momento: datetime | None = None) -> list[tuple[str, str, EstadoEquipo]]:
        return [(e.codigo, e.nombre, e.estado(momento)) for e in self._equipos.values()]

    # Criterio 1: mostrar los equipos disponibles (en un momento o en un tramo)
    def equipos_disponibles(self, inicio: datetime | None = None, fin: datetime | None = None) -> list[Equipo]:
        if inicio is None:
            return [e for e in self._equipos.values() if e.estado() == EstadoEquipo.LIBRE]
        fin = fin or inicio
        if fin == inicio:
            return [e for e in self._equipos.values() if e.estado(inicio) == EstadoEquipo.LIBRE]
        return [e for e in self._equipos.values() if e.esta_libre(inicio, fin)]

    # Criterios 3, 4 y 5: reservar actualiza el estado, sin solapes y solo usuarios validados
    def reservar(self, usuario: Usuario, codigo: str, inicio: datetime, fin: datetime) -> Reserva:
        if not usuario.puede_reservar():
            raise ReservaError("El usuario tiene que estar registrado y validado para reservar")
        if fin <= inicio:
            raise ReservaError("La hora de fin debe ser posterior a la de inicio")

        equipo = self.obtener_equipo(codigo)
        if equipo.fuera_de_servicio:
            raise ReservaError(f"El equipo {equipo.nombre} está fuera de servicio")
        if not equipo.esta_libre(inicio, fin):
            raise ReservaError(f"El equipo {equipo.nombre} ya está reservado en ese tramo horario")

        reserva = Reserva(usuario, inicio, fin)
        equipo.reservas.append(reserva)
        return reserva
