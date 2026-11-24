"""Patrón Factory Method para crear profesionales.

`FabricaProfesional` define el método fábrica abstracto `_crear()`.
Cada fábrica concreta decide qué subclase de Profesional se instancia.
El resto del sistema solo pide `FabricaProfesional.para("nutricionista")`
y nunca necesita conocer las clases concretas.
"""

from abc import ABC, abstractmethod

from cdi.modelos.profesional import (Coordinador, Nutricionista, Pedagogo,
                                     Psicologo, TrabajadorSocial)


class FabricaProfesional(ABC):
    _registro = {}

    def __init_subclass__(cls, tipo=None, **kwargs):
        # Cada fábrica concreta se registra sola con su tipo
        super().__init_subclass__(**kwargs)
        if tipo:
            FabricaProfesional._registro[tipo] = cls

    @abstractmethod
    def _crear(self, **datos):
        """Método fábrica: devuelve la instancia concreta."""

    def crear(self, **datos):
        """Operación común a todas las fábricas: crea y valida."""
        profesional = self._crear(**datos)
        if not profesional.items_documentales():
            raise ValueError("Un profesional debe tener al menos un ítem documental")
        return profesional

    @classmethod
    def para(cls, tipo):
        try:
            return cls._registro[tipo]()
        except KeyError:
            raise ValueError(f"Tipo de profesional desconocido: {tipo}") from None

    @classmethod
    def tipos_disponibles(cls):
        return sorted(cls._registro)


class FabricaNutricionista(FabricaProfesional, tipo=Nutricionista.TIPO):
    def _crear(self, **datos):
        return Nutricionista(**datos)


class FabricaPsicologo(FabricaProfesional, tipo=Psicologo.TIPO):
    def _crear(self, **datos):
        return Psicologo(**datos)


class FabricaPedagogo(FabricaProfesional, tipo=Pedagogo.TIPO):
    def _crear(self, **datos):
        return Pedagogo(**datos)


class FabricaTrabajadorSocial(FabricaProfesional, tipo=TrabajadorSocial.TIPO):
    def _crear(self, **datos):
        return TrabajadorSocial(**datos)


class FabricaCoordinador(FabricaProfesional, tipo=Coordinador.TIPO):
    def _crear(self, **datos):
        return Coordinador(**datos)
