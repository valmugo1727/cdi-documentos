"""Ítem documental: cada "título" donde un profesional debe subir un documento."""

from enum import Enum


class Periodicidad(Enum):
    """Cada cuánto se debe entregar el documento."""
    MENSUAL = "Mensual"
    UNICA = "Única vez"


class Alcance(Enum):
    """Si el documento es general del CDI o se carga uno por cada niño."""
    GENERAL = "General"
    POR_NINO = "Por niño"


class ItemDocumental:
    """Representa un requisito documental de un profesional.

    Ejemplo: para la nutricionista, "Carné de vacunación" es un ítem
    con alcance POR_NINO y periodicidad UNICA.
    """

    def __init__(self, codigo, titulo, descripcion,
                 periodicidad=Periodicidad.MENSUAL,
                 alcance=Alcance.GENERAL,
                 extensiones=(".pdf", ".jpg", ".jpeg", ".png")):
        if not codigo or not titulo:
            raise ValueError("El ítem necesita código y título")
        self.__codigo = codigo
        self.__titulo = titulo
        self.__descripcion = descripcion
        self.__periodicidad = periodicidad
        self.__alcance = alcance
        self.__extensiones = tuple(e.lower() for e in extensiones)

    # --- Propiedades de solo lectura (encapsulamiento) ---
    @property
    def codigo(self):
        return self.__codigo

    @property
    def titulo(self):
        return self.__titulo

    @property
    def descripcion(self):
        return self.__descripcion

    @property
    def periodicidad(self):
        return self.__periodicidad

    @property
    def alcance(self):
        return self.__alcance

    @property
    def extensiones(self):
        return self.__extensiones

    @property
    def es_por_nino(self):
        return self.__alcance == Alcance.POR_NINO

    @property
    def es_mensual(self):
        return self.__periodicidad == Periodicidad.MENSUAL

    def acepta_archivo(self, nombre_archivo):
        """Indica si la extensión del archivo está permitida para este ítem."""
        nombre = (nombre_archivo or "").lower()
        return any(nombre.endswith(ext) for ext in self.__extensiones)

    def __eq__(self, otro):
        return isinstance(otro, ItemDocumental) and otro.codigo == self.codigo

    def __hash__(self):
        return hash(self.__codigo)

    def __repr__(self):
        return f"ItemDocumental({self.__codigo!r}, {self.__titulo!r})"
