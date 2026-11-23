# SG-CICT · HU1 · Registro de investigadores con acreditación

Backend Python (Flask + Firebase Admin / Firestore) y frontend HTML5/CSS/JS, servido por el mismo Flask.

## Puesta en marcha
1. Crea un proyecto en Firebase, activa **Firestore** y **Authentication (correo/contraseña)**.
2. Descarga la clave de cuenta de servicio como `backend/serviceAccountKey.json`.
3. `cd backend && cp .env.example .env` y rellena los valores (incluida la config web de Firebase).
4. `pip install -r requirements.txt`
5. Despliega reglas e índices: `firebase deploy --only firestore:rules,firestore:indexes`
6. `python seed.py` (crea un admin y 3 perfiles UCO de ejemplo)
7. `python app.py` → http://localhost:5000  (producción: `gunicorn -w 3 wsgi:app`)

## Modelo de datos (Firestore)
| Colección | Doc ID | Campos principales |
|---|---|---|
| `perfiles_uco` (padrón institucional) | número de acreditación | nombre, email_institucional, departamento, centro, activo, vinculado_a (uid o null) |
| `solicitudes_registro` | sha256(email)[:40] | email, nombre, apellidos, institucion, acreditacion, tipo_declarado, **tipo** (uco/externo), **prioridad** (0 UCO, 1 externo), verificacion_uco, perfil_uco_id, **estado** (pendiente/aprobada/rechazada), uid, intentos, creado_en, revisado_por, revisado_en, motivo_rechazo |
| `usuarios` | uid de Firebase Auth | email, nombre, apellidos, tipo, prioridad, rol (investigador/admin), estado (activo/suspendido), acreditacion, perfil_uco_id, institucion, departamento, centro, solicitud_id |
| `auditoria` | auto | evento, datos, fecha |

## API
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/registro` | 201 solicitud creada · 200 solicitud ya en revisión · **409 ya registrado (+ aviso y redirect al login)** · 422 validación |
| GET | `/api/admin/solicitudes?estado=pendiente` | Cola ordenada: UCO primero, luego externos (FIFO) |
| POST | `/api/admin/solicitudes/<id>/aprobar` | Body opcional `{"forzar": true, "motivo": "..."}` |
| POST | `/api/admin/solicitudes/<id>/rechazar` | Body `{"motivo": "..."}` |

Rutas admin: cabecera `Authorization: Bearer <ID token de Firebase de un admin>`.

## Reglas de negocio de la HU1
- Usuario con ficha en `usuarios` → 409, aviso informativo y redirección a `/login.html?aviso=ya_registrado&email=...`.
- Usuario nuevo → solicitud `pendiente` creada de forma atómica (transacción, una por email) + cuenta de Auth **deshabilitada** hasta aprobar.
- La prioridad UCO se decide en servidor: solo si la acreditación existe, está activa, no está vinculada y el correo es del dominio UCO o coincide con el padrón.
- No se puede aprobar un externo mientras haya UCO pendientes, salvo `forzar` con motivo (queda registrado).
- Una solicitud rechazada puede reenviarse (incrementa `intentos`).

## Antes de producción
- Verificación de correo (`generate_email_verification_link`) para confirmar la titularidad del email.
- Limiter con Redis (`storage_uri`) si hay varios workers; HTTPS y CORS cerrado a tu dominio.
- Notificaciones por correo al aprobar/rechazar.

## Estructura de la entrega
- `src/`: código (backend Flask, frontend HTML/CSS/JS, reglas e índices de Firestore). Los comandos `firebase ...` se ejecutan desde esta carpeta.
- `tests/`: pruebas automáticas (unittest, sin dependencias extra).

## Tests
Desde la carpeta que contiene `src/` y `tests/`:

    python -m unittest discover -s tests -v

Los tests no necesitan conexión ni credenciales: sustituyen Firebase (Firestore y Auth) por una versión en memoria (`tests/support.py`).
