# Colecciones de Firestore
COL_USUARIOS = "usuarios"
COL_PERFILES_UCO = "perfiles_uco"
COL_SOLICITUDES = "solicitudes_registro"
COL_AUDITORIA = "auditoria"

# Estados de la solicitud de registro
ESTADO_PENDIENTE = "pendiente"
ESTADO_APROBADA = "aprobada"
ESTADO_RECHAZADA = "rechazada"

# Estados del usuario
USUARIO_ACTIVO = "activo"
USUARIO_SUSPENDIDO = "suspendido"

# Tipo de investigador y prioridad (menor número = se atiende antes)
TIPO_UCO = "uco"
TIPO_EXTERNO = "externo"
PRIORIDAD_UCO = 0
PRIORIDAD_EXTERNO = 1
PRIORIDAD_POR_TIPO = {TIPO_UCO: PRIORIDAD_UCO, TIPO_EXTERNO: PRIORIDAD_EXTERNO}

# Roles
ROL_INVESTIGADOR = "investigador"
ROL_ADMIN = "admin"

# Resultado de verificar la acreditación contra el padrón institucional
VERIF_VERIFICADA = "verificada"
VERIF_NO_APLICA = "no_aplica"
VERIF_NO_ENCONTRADA = "no_encontrada"
VERIF_INACTIVA = "inactiva"
VERIF_EMAIL_NO_COINCIDE = "email_no_coincide"
VERIF_YA_VINCULADA = "ya_vinculada"
