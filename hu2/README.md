
# HU2. Consulta del catálogo de equipos y laboratorios

> COMO investigador, QUIERO consultar el catálogo de equipos y laboratorios disponibles, PARA conocer los recursos de investigación existentes y elegir los más adecuados para mis proyectos.

**Responsable:** Patricia Bocero Padilla  
**Lenguaje:** Python 3.10+

## Estructura

* `src/catalogo.py` – Lógica: `Recurso`, `Catalogo` y el enumerado `TipoRecurso`.
* `src/main.py` – Demo por consola.
* `tests/test_catalogo.py` – Tests de los criterios de validación.

## Cómo ejecutarlo

```bash
cd hu2
python3 src/main.py                         # demo
python3 -m unittest discover -s tests -v    # tests
```

## Criterios de validación

| Criterio | Dónde se cumple | Test |
|---|---|---|
| El investigador puede acceder al catálogo de equipos y laboratorios | `Catalogo.listar_recursos()` | `test_se_puede_consultar_catalogo` |
| El sistema muestra todos los equipos y laboratorios registrados | `Catalogo.listar_recursos()` | `test_muestra_equipos_y_laboratorios`, `test_tambien_muestra_recursos_no_disponibles` |
| El investigador puede consultar la información detallada de cada recurso | `Catalogo.obtener_recurso()` | `test_consulta_detalle_de_un_recurso`, `test_recurso_inexistente` |
| La información incluye nombre, descripción, ubicación, responsable y disponibilidad | `Recurso.informacion()` | `test_detalle_contiene_toda_la_informacion` |
| El catálogo puede consultarse de forma clara y organizada | `Catalogo.listar_recursos()`, `Catalogo.listar_con_disponibilidad()` | `test_catalogo_ordenado_por_tipo_y_nombre`, `test_listado_claro_con_disponibilidad` |