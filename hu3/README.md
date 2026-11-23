# HU3. Consulta de disponibilidad de los equipos

> COMO investigador, QUIERO ver qué equipos están disponibles en cada momento, PARA saber cuáles puedo reservar.

**Responsable:** María Jiménez Escalera
**Lenguaje:** Python 3.10+

## Estructura

* `src/equipos.py` – Lógica: `Equipo`, `Usuario`, `Reserva`, `Catalogo` y el enumerado `EstadoEquipo`.
* `src/main.py` – Demo por consola.
* `tests/test_equipos.py` – Tests de los criterios de validación.

## Cómo ejecutarlo

```bash
cd hu3
python3 src/main.py                         # demo
python3 -m unittest discover -s tests -v    # tests
```

## Criterios de validación

| Criterio | Dónde se cumple | Test |
|---|---|---|
| Mostrar los equipos disponibles | `Catalogo.equipos_disponibles()` | `test_muestra_equipos_disponibles` |
| Ver si un equipo está libre, reservado o no disponible | `Equipo.estado()`, `Catalogo.listar_con_estado()` | `test_muestra_nombre_y_estado` |
| El estado se actualiza al reservar | `Catalogo.reservar()` | `test_estado_se_actualiza_al_reservar` |
| No reservar un equipo ya reservado en ese tramo | `Equipo.esta_libre()`, `Reserva.solapa_con()` | `test_no_reservar_en_tramo_ocupado` |
| Usuario registrado y validado para reservar | `Usuario.puede_reservar()` | `test_usuario_no_registrado_no_reserva`, `test_usuario_no_validado_no_reserva` |
