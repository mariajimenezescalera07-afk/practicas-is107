class Investigador:
    def __init__(self, nombre, correo):
        self.nombre = nombre
        self.correo = correo
        self.validado = False


class SolicitudRegistro:
    def __init__(self, investigador):
        self.investigador = investigador
        self.estado = "PENDIENTE"


class Administrador:
    def __init__(self, nombre):
        self.nombre = nombre


class SistemaSolicitudes:
    def __init__(self):
        self.solicitudes = []

    def crear_solicitud(self, investigador):
        solicitud = SolicitudRegistro(investigador)
        self.solicitudes.append(solicitud)
        return solicitud

    def obtener_solicitudes_pendientes(self):
        return [
            solicitud
            for solicitud in self.solicitudes
            if solicitud.estado == "PENDIENTE"
        ]

    def aprobar_solicitud(self, solicitud):
        solicitud.estado = "APROBADA"
        solicitud.investigador.validado = True

    def rechazar_solicitud(self, solicitud):
        solicitud.estado = "RECHAZADA"
        solicitud.investigador.validado = False

    def puede_realizar_reserva(self, investigador):
        return investigador.validado
