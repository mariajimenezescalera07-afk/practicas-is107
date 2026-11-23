
"""Tests de los criterios de validación de la HU2."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from catalogo import Catalogo, Recurso, TipoRecurso  # noqa: E402


class TestHU2(unittest.TestCase):
    def setUp(self):
        self.catalogo = Catalogo()
        self.catalogo.anadir_recurso(Recurso(
            "EQ01", TipoRecurso.EQUIPO, "Microscopio", "Observación de muestras",
            "Laboratorio A", "Ana", True,
        ))
        self.catalogo.anadir_recurso(Recurso(
            "EQ02", TipoRecurso.EQUIPO, "Centrífuga", "Separación de muestras",
            "Laboratorio B", "Luis", False,
        ))
        self.catalogo.anadir_recurso(Recurso(
            "LAB01", TipoRecurso.LABORATORIO, "Laboratorio de análisis",
            "Análisis de muestras", "Edificio C", "Marta", True,
        ))

    # Criterio 1
    def test_se_puede_consultar_catalogo(self):
        self.assertEqual(len(self.catalogo.listar_recursos()), 3)

    # Criterio 2
    def test_muestra_equipos_y_laboratorios(self):
        recursos = self.catalogo.listar_recursos()
        self.assertEqual({r.codigo for r in recursos}, {"EQ01", "EQ02", "LAB01"})
        self.assertEqual(sum(r.tipo == TipoRecurso.EQUIPO for r in recursos), 2)
        self.assertEqual(sum(r.tipo == TipoRecurso.LABORATORIO for r in recursos), 1)

    def test_tambien_muestra_recursos_no_disponibles(self):
        self.assertIn("EQ02", [r.codigo for r in self.catalogo.listar_recursos()])

    # Criterio 3
    def test_consulta_detalle_de_un_recurso(self):
        recurso = self.catalogo.obtener_recurso("EQ01")
        self.assertEqual(recurso.nombre, "Microscopio")

    def test_recurso_inexistente(self):
        with self.assertRaises(KeyError):
            self.catalogo.obtener_recurso("EQ99")

    # Criterio 4
    def test_detalle_contiene_toda_la_informacion(self):
        detalle = self.catalogo.obtener_recurso("EQ02").informacion()
        self.assertEqual(detalle["nombre"], "Centrífuga")
        self.assertEqual(detalle["descripcion"], "Separación de muestras")
        self.assertEqual(detalle["ubicacion"], "Laboratorio B")
        self.assertEqual(detalle["responsable"], "Luis")
        self.assertEqual(detalle["disponibilidad"], "No disponible")

    # Criterio 5
    def test_catalogo_ordenado_por_tipo_y_nombre(self):
        codigos = [r.codigo for r in self.catalogo.listar_recursos()]
        self.assertEqual(codigos, ["EQ02", "EQ01", "LAB01"])

    def test_listado_claro_con_disponibilidad(self):
        listado = self.catalogo.listar_con_disponibilidad()
        self.assertEqual(listado[0], ("EQ02", "Equipo", "Centrífuga", "No disponible"))


if __name__ == "__main__":
    unittest.main()
