"""Jerarquía de profesionales del CDI.

`Profesional` es una clase abstracta. Cada subclase define (polimorfismo)
cuáles son sus ítems documentales y qué permisos tiene dentro del sistema.
"""

from abc import ABC, abstractmethod

from werkzeug.security import check_password_hash, generate_password_hash

from .item_documental import Alcance, ItemDocumental, Periodicidad

# Extensiones de uso frecuente
PDF_IMAGEN = (".pdf", ".jpg", ".jpeg", ".png")
HOJA_CALCULO = (".xlsx", ".xls", ".csv", ".pdf")
DOCUMENTO = (".pdf", ".docx", ".doc")


class Profesional(ABC):
    """Clase base de todos los profesionales que suben documentos."""

    TIPO = "profesional"          # lo sobrescribe cada subclase
    NOMBRE_CARGO = "Profesional"

    def __init__(self, identificacion, nombres, usuario, clave=None,
                 clave_hash=None, id_=None):
        if not identificacion or not nombres or not usuario:
            raise ValueError("Identificación, nombres y usuario son obligatorios")
        self.__id = id_
        self.__identificacion = str(identificacion)
        self.__nombres = nombres.strip()
        self.__usuario = usuario.strip().lower()
        if clave_hash:
            self.__clave_hash = clave_hash
        elif clave:
            self.__clave_hash = generate_password_hash(clave)
        else:
            raise ValueError("Se requiere una clave")

    # --- Propiedades ---
    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, valor):
        if self.__id is not None:
            raise AttributeError("El id ya fue asignado")
        self.__id = valor

    @property
    def identificacion(self):
        return self.__identificacion

    @property
    def nombres(self):
        return self.__nombres

    @property
    def usuario(self):
        return self.__usuario

    @property
    def clave_hash(self):
        return self.__clave_hash

    # --- Comportamiento común ---
    def verificar_clave(self, clave):
        return check_password_hash(self.__clave_hash, clave)

    def cambiar_clave(self, actual, nueva):
        if not self.verificar_clave(actual):
            raise PermissionError("La clave actual no es correcta")
        if len(nueva) < 6:
            raise ValueError("La nueva clave debe tener al menos 6 caracteres")
        self.__clave_hash = generate_password_hash(nueva)

    def buscar_item(self, codigo):
        """Devuelve el ítem con ese código o None si no le pertenece."""
        for item in self.items_documentales():
            if item.codigo == codigo:
                return item
        return None

    def puede_ver_reportes(self):
        """Por defecto un profesional solo ve sus propios documentos."""
        return False

    # --- Métodos que cada profesional debe implementar ---
    @abstractmethod
    def items_documentales(self):
        """Lista de ítems (títulos) donde este profesional sube documentos."""

    @abstractmethod
    def descripcion_rol(self):
        """Texto corto con la función del profesional en el CDI."""

    def __str__(self):
        return f"{self.NOMBRE_CARGO}: {self.__nombres}"

    def __repr__(self):
        return f"{type(self).__name__}(usuario={self.__usuario!r})"


class Nutricionista(Profesional):
    TIPO = "nutricionista"
    NOMBRE_CARGO = "Nutricionista Dietista"

    _ITEMS = (
        ItemDocumental(
            "NUT-BIEN", "Entrega de Bienestarina",
            "Planilla con la cantidad de Bienestarina entregada a cada padre de familia.",
            Periodicidad.MENSUAL, Alcance.GENERAL, HOJA_CALCULO),
        ItemDocumental(
            "NUT-EDU", "Actas de educación a padres de familia",
            "Actas firmadas de los encuentros educativos en alimentación y nutrición.",
            Periodicidad.MENSUAL, Alcance.GENERAL, PDF_IMAGEN),
        ItemDocumental(
            "NUT-VAC", "Carné de vacunación",
            "Copia del carné de vacunación de cada niño registrado en el CDI.",
            Periodicidad.UNICA, Alcance.POR_NINO, PDF_IMAGEN),
        ItemDocumental(
            "NUT-ANT", "Datos antropométricos",
            "Registro mensual de peso, talla y perímetros de cada niño.",
            Periodicidad.MENSUAL, Alcance.POR_NINO, HOJA_CALCULO),
        ItemDocumental(
            "NUT-NOV", "Novedades especiales del mes",
            "Casos de malnutrición, remisiones o situaciones especiales del mes.",
            Periodicidad.MENSUAL, Alcance.GENERAL, DOCUMENTO),
    )

    def items_documentales(self):
        return list(self._ITEMS)

    def descripcion_rol(self):
        return "Seguimiento nutricional, complementación alimentaria y educación a familias."


class Psicologo(Profesional):
    TIPO = "psicologo"
    NOMBRE_CARGO = "Psicólogo(a)"

    _ITEMS = (
        ItemDocumental(
            "PSI-VAL", "Valoración psicosocial inicial",
            "Valoración de ingreso de cada niño y su entorno familiar.",
            Periodicidad.UNICA, Alcance.POR_NINO, DOCUMENTO),
        ItemDocumental(
            "PSI-TAL", "Actas de talleres con familias",
            "Actas y listados de asistencia de los talleres de crianza.",
            Periodicidad.MENSUAL, Alcance.GENERAL, PDF_IMAGEN),
        ItemDocumental(
            "PSI-REM", "Remisiones a otras entidades",
            "Remisiones realizadas a EPS, ICBF u otras entidades en el mes.",
            Periodicidad.MENSUAL, Alcance.GENERAL, DOCUMENTO),
        ItemDocumental(
            "PSI-NOV", "Novedades especiales del mes",
            "Situaciones relevantes del componente psicosocial.",
            Periodicidad.MENSUAL, Alcance.GENERAL, DOCUMENTO),
    )

    def items_documentales(self):
        return list(self._ITEMS)

    def descripcion_rol(self):
        return "Acompañamiento psicosocial a niños y familias."


class Pedagogo(Profesional):
    TIPO = "pedagogo"
    NOMBRE_CARGO = "Docente / Pedagogo(a)"

    _ITEMS = (
        ItemDocumental(
            "PED-PLA", "Planeación pedagógica",
            "Planeación de experiencias pedagógicas del mes.",
            Periodicidad.MENSUAL, Alcance.GENERAL, DOCUMENTO),
        ItemDocumental(
            "PED-SEG", "Seguimiento al desarrollo",
            "Observación y seguimiento al desarrollo de cada niño.",
            Periodicidad.MENSUAL, Alcance.POR_NINO, DOCUMENTO),
        ItemDocumental(
            "PED-ASI", "Registro de asistencia",
            "Consolidado mensual de asistencia de los niños.",
            Periodicidad.MENSUAL, Alcance.GENERAL, HOJA_CALCULO),
        ItemDocumental(
            "PED-NOV", "Novedades especiales del mes",
            "Situaciones relevantes del componente pedagógico.",
            Periodicidad.MENSUAL, Alcance.GENERAL, DOCUMENTO),
    )

    def items_documentales(self):
        return list(self._ITEMS)

    def descripcion_rol(self):
        return "Planeación y seguimiento de las experiencias pedagógicas."


class TrabajadorSocial(Profesional):
    TIPO = "trabajador_social"
    NOMBRE_CARGO = "Trabajador(a) Social"

    _ITEMS = (
        ItemDocumental(
            "TS-CAR", "Ficha de caracterización familiar",
            "Caracterización socioeconómica de la familia de cada niño.",
            Periodicidad.UNICA, Alcance.POR_NINO, DOCUMENTO),
        ItemDocumental(
            "TS-VIS", "Visitas domiciliarias",
            "Informes de las visitas domiciliarias realizadas en el mes.",
            Periodicidad.MENSUAL, Alcance.GENERAL, DOCUMENTO),
        ItemDocumental(
            "TS-NOV", "Novedades especiales del mes",
            "Situaciones relevantes del componente familiar y comunitario.",
            Periodicidad.MENSUAL, Alcance.GENERAL, DOCUMENTO),
    )

    def items_documentales(self):
        return list(self._ITEMS)

    def descripcion_rol(self):
        return "Trabajo con familias, redes de apoyo y comunidad."


class Coordinador(Profesional):
    TIPO = "coordinador"
    NOMBRE_CARGO = "Coordinador(a) del CDI"

    _ITEMS = (
        ItemDocumental(
            "COO-INF", "Informe mensual de gestión",
            "Informe consolidado del CDI para el operador o el ICBF.",
            Periodicidad.MENSUAL, Alcance.GENERAL, DOCUMENTO),
        ItemDocumental(
            "COO-COM", "Actas de comité técnico",
            "Actas de las reuniones del equipo interdisciplinario.",
            Periodicidad.MENSUAL, Alcance.GENERAL, PDF_IMAGEN),
    )

    def items_documentales(self):
        return list(self._ITEMS)

    def descripcion_rol(self):
        return "Coordina el equipo y revisa el cumplimiento documental."

    def puede_ver_reportes(self):
        # Polimorfismo: el coordinador sí tiene acceso a los reportes globales
        return True
