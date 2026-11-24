"""Datos de ejemplo para probar la aplicación la primera vez."""

from datetime import date

from cdi.modelos import Nino
from cdi.patrones import FabricaProfesional
from cdi.persistencia import RepositorioNinos, RepositorioProfesionales

CLAVE_DEMO = "cdi2026"

PROFESIONALES_DEMO = [
    ("nutricionista", "1085000001", "Valentina Rosero", "nutricion"),
    ("psicologo", "1085000002", "Laura Benavides", "psicologia"),
    ("pedagogo", "1085000003", "Carlos Muñoz", "pedagogia"),
    ("trabajador_social", "1085000004", "Diana Erazo", "trabajosocial"),
    ("coordinador", "1085000005", "Andrea Guerrero", "coordinacion"),
]

NINOS_DEMO = [
    ("1080100001", "Sofía Martínez López", date(2022, 3, 14), "María López", "3101234567"),
    ("1080100002", "Mateo Ortega Ruiz", date(2021, 9, 2), "Luis Ortega", "3112345678"),
    ("1080100003", "Isabella Chamorro Paz", date(2023, 1, 20), "Rosa Paz", "3123456789"),
    ("1080100004", "Samuel Ibarra Díaz", date(2022, 7, 8), "Jorge Ibarra", "3134567890"),
]


def cargar_datos_demo():
    """Crea usuarios y niños de ejemplo solo si la base está vacía."""
    repo_prof = RepositorioProfesionales()
    if repo_prof.contar() > 0:
        return False
    for tipo, identificacion, nombres, usuario in PROFESIONALES_DEMO:
        profesional = FabricaProfesional.para(tipo).crear(
            identificacion=identificacion, nombres=nombres,
            usuario=usuario, clave=CLAVE_DEMO)
        repo_prof.guardar(profesional)
    repo_ninos = RepositorioNinos()
    for datos in NINOS_DEMO:
        repo_ninos.guardar(Nino(*datos))
    return True
