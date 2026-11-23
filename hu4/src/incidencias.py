class Usuario:
    def __init__(self, nombre, rol):
        self.nombre = nombre
        self.rol = rol


class Equipo:
    def __init__(self, nombre):
        self.nombre = nombre
        self.disponible = True
        self.averiado = False
        self.descripcion = ""

    def poner_incidencia(self, descripcion):
        self.averiado = True
        self.disponible = False
        self.descripcion = descripcion

    def reparar(self):
        self.averiado = False
        self.disponible = True
        self.descripcion = ""


class SistemaIncidencias:
    def __init__(self):
        self.equipos_averiados = []

    def registrar_incidencia(self, usuario, equipo, descripcion):

        if usuario.rol not in ["investigador", "tecnico"]:
            raise ValueError("Rol no permitido")

        equipo.poner_incidencia(descripcion)

        if equipo not in self.equipos_averiados:
            self.equipos_averiados.append(equipo)

    def obtener_equipos_averiados(self, usuario):

        if usuario.rol != "tecnico":
            raise PermissionError(
                "Solo los tecnicos pueden consultar incidencias"
            )

        return self.equipos_averiados

    def reparar_equipo(self, equipo):

        equipo.reparar()

        if equipo in self.equipos_averiados:
            self.equipos_averiados.remove(equipo)

    def reservar_equipo(self, equipo):

        if equipo.averiado:
            raise Exception(
                "No se puede reservar un equipo averiado"
            )

        return True
