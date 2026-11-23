"""Tests de los criterios de validación de la HU3."""

import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from equipos import Catalogo, Equipo, EstadoEquipo, ReservaError, Usuario  # noqa: E402

D = datetime(2026, 11, 24)


def h(hora: int) -> datetime:
    return D.replace(hour=hora)


class TestHU3(unittest.TestCase):
    def setUp(self):
        self.catalogo = Catalogo()
        self.catalogo.anadir_equipo(Equipo("EQ01", "Microscopio"))
        self.catalogo.anadir_equipo(Equipo("EQ02", "Espectrómetro"))
        self.catalogo.anadir_equipo(Equipo("EQ03", "Centrifugadora", fuera_de_servicio=True))
        self.usuario = Usuario("Ana", registrado=True, validado=True)

    # Criterio 1
    def test_muestra_equipos_disponibles(self):
        disponibles = [e.codigo for e in self.catalogo.equipos_disponibles(h(10))]
        self.assertEqual(disponibles, ["EQ01", "EQ02"])

    # Criterio 2
    def test_muestra_nombre_y_estado(self):
        self.catalogo.reservar(self.usuario, "EQ01", h(9), h(11))
        estados = {c: (n, e) for c, n, e in self.catalogo.listar_con_estado(h(10))}
        self.assertEqual(estados["EQ01"], ("Microscopio", EstadoEquipo.RESERVADO))
        self.assertEqual(estados["EQ02"], ("Espectrómetro", EstadoEquipo.LIBRE))
        self.assertEqual(estados["EQ03"], ("Centrifugadora", EstadoEquipo.FUERA_DE_SERVICIO))

    # Criterio 3
    def test_estado_se_actualiza_al_reservar(self):
        equipo = self.catalogo.obtener_equipo("EQ02")
        self.assertEqual(equipo.estado(h(10)), EstadoEquipo.LIBRE)
        self.catalogo.reservar(self.usuario, "EQ02", h(10), h(12))
        self.assertEqual(equipo.estado(h(10)), EstadoEquipo.RESERVADO)
        self.assertNotIn(equipo, self.catalogo.equipos_disponibles(h(10)))
        self.assertEqual(equipo.estado(h(12)), EstadoEquipo.LIBRE)  # al acabar vuelve a estar libre

    # Criterio 4
    def test_no_reservar_en_tramo_ocupado(self):
        self.catalogo.reservar(self.usuario, "EQ01", h(10), h(12))
        with self.assertRaises(ReservaError):
            self.catalogo.reservar(self.usuario, "EQ01", h(11), h(13))

    def test_si_reservar_tramo_contiguo(self):
        self.catalogo.reservar(self.usuario, "EQ01", h(10), h(12))
        self.catalogo.reservar(self.usuario, "EQ01", h(12), h(13))  # no solapa

    def test_no_reservar_fuera_de_servicio(self):
        with self.assertRaises(ReservaError):
            self.catalogo.reservar(self.usuario, "EQ03", h(10), h(11))

    # Criterio 5
    def test_usuario_no_registrado_no_reserva(self):
        with self.assertRaises(ReservaError):
            self.catalogo.reservar(Usuario("Pepe"), "EQ01", h(10), h(11))

    def test_usuario_no_validado_no_reserva(self):
        with self.assertRaises(ReservaError):
            self.catalogo.reservar(Usuario("Luis", registrado=True), "EQ01", h(10), h(11))


if __name__ == "__main__":
    unittest.main()
