"""Reporte de cumplimiento documental para el coordinador."""

from dataclasses import dataclass

from cdi.persistencia import RepositorioProfesionales


@dataclass
class FilaCumplimiento:
    profesional: object
    estados: list

    @property
    def porcentaje(self):
        if not self.estados:
            return 100
        return round(sum(e.porcentaje for e in self.estados) / len(self.estados))

    @property
    def pendientes(self):
        return [e for e in self.estados if not e.completo]


class ReporteCumplimiento:
    def __init__(self, gestor):
        self.__gestor = gestor
        self.__profesionales = RepositorioProfesionales()

    def generar(self, solicitante, periodo):
        if not solicitante.puede_ver_reportes():
            raise PermissionError("Solo la coordinación puede ver este reporte")
        filas = [FilaCumplimiento(p, self.__gestor.estado_items(p, periodo))
                 for p in self.__profesionales.listar()]
        filas.sort(key=lambda f: f.porcentaje)
        return filas

    @staticmethod
    def promedio_general(filas):
        if not filas:
            return 0
        return round(sum(f.porcentaje for f in filas) / len(filas))
