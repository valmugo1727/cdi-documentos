"""Patrón Observer.

Cuando se sube o elimina un documento, el gestor documental (sujeto)
avisa a todos sus observadores: la bitácora de auditoría, el notificador
de mensajes en pantalla, etc. Se pueden agregar observadores nuevos
sin modificar el gestor.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Evento:
    tipo: str                 # "documento_subido", "documento_eliminado", ...
    usuario: str
    detalle: str
    datos: dict = field(default_factory=dict)
    fecha: datetime = field(default_factory=lambda: datetime.now().replace(microsecond=0))


class Observador(ABC):
    @abstractmethod
    def actualizar(self, evento):
        """Recibe el evento notificado por el sujeto."""


class Sujeto:
    def __init__(self):
        self.__observadores = []

    def suscribir(self, observador):
        if not isinstance(observador, Observador):
            raise TypeError("Solo se pueden suscribir objetos Observador")
        if observador not in self.__observadores:
            self.__observadores.append(observador)

    def desuscribir(self, observador):
        if observador in self.__observadores:
            self.__observadores.remove(observador)

    @property
    def observadores(self):
        return tuple(self.__observadores)

    def notificar(self, evento):
        for observador in self.__observadores:
            observador.actualizar(evento)
