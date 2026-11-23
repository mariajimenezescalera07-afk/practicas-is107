import pytest

from src.incidencias import (
    Usuario,
    Equipo,
    SistemaIncidencias
)


def test_investigador_puede_poner_incidencia():

    sistema = SistemaIncidencias()

    investigador = Usuario(
        "Investigador1",
        "investigador"
    )

    equipo = Equipo(
        "Equipo1"
    )

    sistema.registrar_incidencia(
        investigador,
        equipo,
        "Problema detectado"
    )

    assert equipo.averiado


def test_tecnico_puede_poner_incidencia():

    sistema = SistemaIncidencias()

    tecnico = Usuario(
        "Tecnico1",
        "tecnico"
    )

    equipo = Equipo(
        "Equipo2"
    )

    sistema.registrar_incidencia(
        tecnico,
        equipo,
        "Problema detectado"
    )

    assert equipo.averiado


def test_investigador_no_ve_averiados():

    sistema = SistemaIncidencias()

    investigador = Usuario(
        "Investigador1",
        "investigador"
    )

    with pytest.raises(
        PermissionError
    ):
        sistema.obtener_equipos_averiados(
            investigador
        )


def test_equipo_averiado_no_reservable():

    sistema = SistemaIncidencias()

    usuario = Usuario(
        "Investigador1",
        "investigador"
    )

    equipo = Equipo(
        "Equipo3"
    )

    sistema.registrar_incidencia(
        usuario,
        equipo,
        "Problema detectado"
    )

    with pytest.raises(
        Exception
    ):
        sistema.reservar_equipo(
            equipo
        )


def test_equipo_reparado_vuelve_disponible():

    sistema = SistemaIncidencias()

    tecnico = Usuario(
        "Tecnico1",
        "tecnico"
    )

    equipo = Equipo(
        "Equipo4"
    )

    sistema.registrar_incidencia(
        tecnico,
        equipo,
        "Problema detectado"
    )

    sistema.reparar_equipo(
        equipo
    )

    assert equipo.disponible
    assert not equipo.averiado
