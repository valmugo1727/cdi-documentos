"""Documento cargado por un profesional en uno de sus ítems."""

import re
from datetime import datetime

PATRON_PERIODO = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class Documento:
    def __init__(self, codigo_item, profesional_id, periodo, nombre_original,
                 ruta_archivo, nino_id=None, observaciones="",
                 fecha_carga=None, id_=None):
        if not PATRON_PERIODO.match(periodo or ""):
            raise ValueError("El periodo debe tener el formato AAAA-MM")
        self.__id = id_
        self.__codigo_item = codigo_item
        self.__profesional_id = profesional_id
        self.__periodo = periodo
        self.__nombre_original = nombre_original
        self.__ruta_archivo = ruta_archivo
        self.__nino_id = nino_id
        self.__observaciones = (observaciones or "").strip()
        self.__fecha_carga = fecha_carga or datetime.now().replace(microsecond=0)

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, valor):
        if self.__id is not None:
            raise AttributeError("El id ya fue asignado")
        self.__id = valor

    @property
    def codigo_item(self):
        return self.__codigo_item

    @property
    def profesional_id(self):
        return self.__profesional_id

    @property
    def periodo(self):
        return self.__periodo

    @property
    def nombre_original(self):
        return self.__nombre_original

    @property
    def ruta_archivo(self):
        return self.__ruta_archivo

    @property
    def nino_id(self):
        return self.__nino_id

    @property
    def observaciones(self):
        return self.__observaciones

    @property
    def fecha_carga(self):
        return self.__fecha_carga

    def __repr__(self):
        return f"Documento({self.__codigo_item}, {self.__periodo}, {self.__nombre_original!r})"
