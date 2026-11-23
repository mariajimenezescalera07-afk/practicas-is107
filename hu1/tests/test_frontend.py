"""Comprobaciones estáticas del frontend (sin navegador)."""
import os
import re
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "frontend"))


def leer(nombre):
    with open(os.path.join(RAIZ, nombre), encoding="utf-8") as f:
        return f.read()


class FrontendTest(unittest.TestCase):
    def test_todos_los_ids_que_usa_app_js_existen_en_index_html(self):
        html, js = leer("index.html"), leer("app.js")
        usados = set(re.findall(r'\$\("([^"]+)"\)', js))
        existentes = set(re.findall(r'id="([^"]+)"', html))
        self.assertEqual(usados - existentes, set())

    def test_el_formulario_incluye_los_campos_de_la_hu1(self):
        html = leer("index.html")
        for campo in ("nombre", "apellidos", "email", "acreditacion", "institucion",
                      "password", "password2", "acepta"):
            self.assertIn(f'id="{campo}"', html, campo)

    def test_los_avisos_son_accesibles_para_lectores_de_pantalla(self):
        self.assertIn('aria-live="polite"', leer("index.html"))
        self.assertIn('aria-live="polite"', leer("login.html"))

    def test_el_frontend_trata_el_caso_ya_registrado_y_redirige(self):
        js = leer("app.js")
        self.assertIn('"ya_registrado"', js)
        self.assertIn("window.location.assign", js)

    def test_el_login_lee_el_aviso_de_la_url(self):
        self.assertIn("ya_registrado", leer("login.html"))

    def test_los_avisos_se_pintan_con_textcontent_nunca_con_innerhtml(self):
        self.assertNotIn("innerHTML", leer("app.js"))
        self.assertNotIn("innerHTML", leer("login.html"))


if __name__ == "__main__":
    unittest.main()
