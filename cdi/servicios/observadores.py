"""Observadores concretos del gestor documental."""

from collections import defaultdict, deque

from cdi.patrones import Observador
from cdi.persistencia import RepositorioBitacora


class BitacoraAuditoria(Observador):
    """Guarda en la base de datos cada acción (trazabilidad para auditorías)."""

    def __init__(self):
        self.__repo = RepositorioBitacora()

    def actualizar(self, evento):
        self.__repo.registrar(evento.fecha, evento.usuario, evento.tipo, evento.detalle)


class NotificadorPantalla(Observador):
    """Acumula mensajes por usuario para mostrarlos en la interfaz web."""

    MENSAJES = {
        "documento_subido": "Documento cargado: {detalle}",
        "documento_eliminado": "Documento eliminado: {detalle}",
    }

    def __init__(self, maximo_por_usuario=20):
        self.__pendientes = defaultdict(lambda: deque(maxlen=maximo_por_usuario))

    def actualizar(self, evento):
        plantilla = self.MENSAJES.get(evento.tipo, "{detalle}")
        self.__pendientes[evento.usuario].append(plantilla.format(detalle=evento.detalle))

    def tomar_mensajes(self, usuario):
        """Devuelve y limpia los mensajes del usuario."""
        mensajes = list(self.__pendientes[usuario])
        self.__pendientes[usuario].clear()
        return mensajes


class ContadorEstadisticas(Observador):
    """Lleva un conteo en memoria de los eventos (útil para el tablero)."""

    def __init__(self):
        self.__conteo = defaultdict(int)

    def actualizar(self, evento):
        self.__conteo[evento.tipo] += 1

    def total(self, tipo):
        return self.__conteo[tipo]
