# HU1 - Registro de investigadores de la UCO

## Historia de Usuario

**COMO** investigador de la UCO,

**QUIERO** registrarme con mi acreditación,

**PARA** tener acceso a la plataforma y preferencia a la hora de reservar material sobre investigadores externos.

---

## Criterios de validación

1. El sistema comprueba si el investigador ya está registrado.
2. Si el investigador ya está registrado, se muestra una notificación informativa y se redirige al inicio de sesión.
3. Si el investigador no está registrado, se genera automáticamente una solicitud de registro.
4. La solicitud queda pendiente de aprobación por parte de los administradores.
5. Los investigadores de la UCO tienen prioridad respecto a los investigadores externos.

---

## Estructura del proyecto

```text
src/
├── registro_uco.py
└── main.py

tests/
└── test_registro_uco.py