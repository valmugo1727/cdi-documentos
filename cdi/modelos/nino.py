"""Niño o niña matriculado en el CDI."""

from datetime import date


class Nino:
    def __init__(self, documento, nombres, fecha_nacimiento, acudiente,
                 telefono_acudiente="", id_=None):
        if not documento or not nombres:
            raise ValueError("Documento y nombres son obligatorios")
        if isinstance(fecha_nacimiento, str):
            fecha_nacimiento = date.fromisoformat(fecha_nacimiento)
        if fecha_nacimiento > date.today():
            raise ValueError("La fecha de nacimiento no puede estar en el futuro")
        self.__id = id_
        self.__documento = str(documento).strip()
        self.__nombres = nombres.strip()
        self.__fecha_nacimiento = fecha_nacimiento
        self.__acudiente = acudiente.strip()
        self.__telefono_acudiente = telefono_acudiente.strip()

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, valor):
        if self.__id is not None:
            raise AttributeError("El id ya fue asignado")
        self.__id = valor

    @property
    def documento(self):
        return self.__documento

    @property
    def nombres(self):
        return self.__nombres

    @property
    def fecha_nacimiento(self):
        return self.__fecha_nacimiento

    @property
    def acudiente(self):
        return self.__acudiente

    @property
    def telefono_acudiente(self):
        return self.__telefono_acudiente

    def edad_en_meses(self, hoy=None):
        """Edad en meses cumplidos (útil para la valoración nutricional)."""
        hoy = hoy or date.today()
        meses = (hoy.year - self.__fecha_nacimiento.year) * 12
        meses += hoy.month - self.__fecha_nacimiento.month
        if hoy.day < self.__fecha_nacimiento.day:
            meses -= 1
        return max(meses, 0)

    def __str__(self):
        return f"{self.__nombres} ({self.__documento})"
