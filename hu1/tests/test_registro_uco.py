"""
Tests de los criterios de validación de la HU1.
"""
import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "src")
)

from registro_uco import (  # noqa: E402
    SistemaRegistro,
    Investigador,
    EstadoSolicitud,
    RegistroError
)


class TestHU1(unittest.TestCase):

    def setUp(self):
        self.sistema = SistemaRegistro()
        self.investigador = Investigador(
            "Ana López",
            "UCO001"
        )

    # Criterio 1
    def test_usuario_ya_registrado(self):
        self.sistema.registrar_usuario(self.investigador)

        mensaje = self.sistema.registrar_usuario(
            self.investigador
        )

        self.assertIn(
            "ya está registrado",
            mensaje
        )

    # Criterio 2
    def test_se_envia_solicitud_si_no_esta_registrado(self):
        mensaje = self.sistema.registrar_usuario(
            self.investigador
        )

        self.assertIn(
            "Solicitud de registro enviada",
            mensaje
        )

    # Criterio 3
    def test_solicitud_queda_pendiente(self):
        self.sistema.registrar_usuario(
            self.investigador
        )

        solicitud = self.sistema.obtener_solicitud(
            "UCO001"
        )

        self.assertEqual(
            solicitud.estado,
            EstadoSolicitud.PENDIENTE
        )

    # Criterio 4
    def test_investigador_uco_tiene_prioridad(self):
        self.sistema.registrar_usuario(
            self.investigador
        )

        solicitud = self.sistema.obtener_solicitud(
            "UCO001"
        )

        self.assertEqual(
            solicitud.investigador.prioridad,
            1
        )

    def test_error_si_no_existe_solicitud(self):
        with self.assertRaises(RegistroError):
            self.sistema.obtener_solicitud(
                "NO_EXISTE"
            )


if __name__ == "__main__":
    unittest.main()