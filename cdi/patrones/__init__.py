"""Patrones de diseño usados en el proyecto."""

from .singleton import ConexionBD
from .fabrica import FabricaProfesional
from .observador import Evento, Observador, Sujeto

__all__ = ["ConexionBD", "FabricaProfesional", "Evento", "Observador", "Sujeto"]
