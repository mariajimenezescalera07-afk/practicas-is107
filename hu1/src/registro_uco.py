"""
HU1. Registrarse como investigador de la UCO

COMO investigador de la UCO,
QUIERO registrarme con mi acreditación,
PARA tener acceso a la plataforma y preferencia a la hora
de reservar material sobre investigadores externos.

Criterios de validación:
1. Si el investigador ya está registrado, se informa y se redirige al inicio de sesión.
2. Si no está registrado, se genera una solicitud de registro.
3. La solicitud queda pendiente de aprobación por los administradores.
4. Los investigadores internos tienen prioridad sobre los externos.
"""

from dataclasses import dataclass
from enum import Enum


class RegistroError(Exception):
    """Error relacionado con el registro."""


class EstadoSolicitud(Enum):
    PENDIENTE = "Pendiente"
    APROBADA = "Aprobada"
    RECHAZADA = "Rechazada"


@dataclass
class Investigador:
    nombre: str
    acreditacion: str
    registrado: bool = False
    prioridad: int = 0


@dataclass
class SolicitudRegistro:
    investigador: Investigador
    estado: EstadoSolicitud = EstadoSolicitud.PENDIENTE
    prioridad: int = 1  # Investigadores UCO tienen prioridad


class SistemaRegistro:
    def __init__(self):
        self._usuarios = {}
        self.solicitudes = []

    def registrar_usuario(self, investigador: Investigador) -> str:
        if investigador.acreditacion in self._usuarios:
            return (
                "El investigador ya está registrado. "
                "Redirigiendo al inicio de sesión."
            )

        solicitud = SolicitudRegistro(investigador)
        self.solicitudes.append(solicitud)

        self._usuarios[investigador.acreditacion] = investigador

        return (
            "Solicitud de registro enviada correctamente. "
            "Pendiente de aprobación."
        )

    def existe_usuario(self, acreditacion: str) -> bool:
        return acreditacion in self._usuarios

    def obtener_solicitud(self, acreditacion: str) -> SolicitudRegistro:
        for solicitud in self.solicitudes:
            if solicitud.investigador.acreditacion == acreditacion:
                return solicitud

        raise RegistroError("No existe solicitud para esa acreditación")