"""Repositorios: traducen entre objetos del dominio y filas de SQLite.

Todos heredan de `RepositorioBase`, que guarda la conexión (Singleton)
y define la interfaz común. Cada subclase sabe convertir una fila en
su objeto correspondiente (`_a_objeto`).
"""

from abc import ABC, abstractmethod
from datetime import datetime

from cdi.modelos import Documento, Nino
from cdi.patrones import ConexionBD, FabricaProfesional

from .esquema import ESQUEMA


def inicializar_bd(ruta="cdi.db"):
    """Crea (si no existen) las tablas y devuelve la conexión única."""
    bd = ConexionBD(ruta)
    bd.ejecutar_script(ESQUEMA)
    return bd


class RepositorioBase(ABC):
    TABLA = None

    def __init__(self):
        self._bd = ConexionBD()   # siempre la misma instancia

    @abstractmethod
    def _a_objeto(self, fila):
        """Convierte una fila de la BD en un objeto del dominio."""

    def obtener(self, id_):
        fila = self._bd.consultar_uno(f"SELECT * FROM {self.TABLA} WHERE id = ?", (id_,))
        return self._a_objeto(fila) if fila else None

    def listar(self):
        filas = self._bd.consultar(f"SELECT * FROM {self.TABLA} ORDER BY id")
        return [self._a_objeto(f) for f in filas]

    def contar(self):
        return self._bd.consultar_uno(f"SELECT COUNT(*) AS n FROM {self.TABLA}")["n"]

    def eliminar(self, id_):
        self._bd.ejecutar(f"DELETE FROM {self.TABLA} WHERE id = ?", (id_,))


class RepositorioProfesionales(RepositorioBase):
    TABLA = "profesionales"

    def _a_objeto(self, fila):
        # Se usa la fábrica: el repositorio no conoce las subclases concretas
        fabrica = FabricaProfesional.para(fila["tipo"])
        return fabrica.crear(identificacion=fila["identificacion"],
                             nombres=fila["nombres"],
                             usuario=fila["usuario"],
                             clave_hash=fila["clave_hash"],
                             id_=fila["id"])

    def guardar(self, profesional):
        if profesional.id is None:
            profesional.id = self._bd.ejecutar(
                "INSERT INTO profesionales (tipo, identificacion, nombres, usuario, clave_hash) "
                "VALUES (?, ?, ?, ?, ?)",
                (profesional.TIPO, profesional.identificacion, profesional.nombres,
                 profesional.usuario, profesional.clave_hash))
        else:
            self._bd.ejecutar(
                "UPDATE profesionales SET nombres = ?, clave_hash = ? WHERE id = ?",
                (profesional.nombres, profesional.clave_hash, profesional.id))
        return profesional

    def buscar_por_usuario(self, usuario):
        fila = self._bd.consultar_uno(
            "SELECT * FROM profesionales WHERE usuario = ?", ((usuario or "").strip().lower(),))
        return self._a_objeto(fila) if fila else None


class RepositorioNinos(RepositorioBase):
    TABLA = "ninos"

    def _a_objeto(self, fila):
        return Nino(fila["documento"], fila["nombres"], fila["fecha_nacimiento"],
                    fila["acudiente"], fila["telefono_acudiente"], id_=fila["id"])

    def guardar(self, nino):
        if self.buscar_por_documento(nino.documento):
            raise ValueError(f"Ya existe un niño con documento {nino.documento}")
        nino.id = self._bd.ejecutar(
            "INSERT INTO ninos (documento, nombres, fecha_nacimiento, acudiente, telefono_acudiente) "
            "VALUES (?, ?, ?, ?, ?)",
            (nino.documento, nino.nombres, nino.fecha_nacimiento.isoformat(),
             nino.acudiente, nino.telefono_acudiente))
        return nino

    def buscar_por_documento(self, documento):
        fila = self._bd.consultar_uno("SELECT * FROM ninos WHERE documento = ?", (documento,))
        return self._a_objeto(fila) if fila else None

    def listar(self):
        filas = self._bd.consultar("SELECT * FROM ninos ORDER BY nombres")
        return [self._a_objeto(f) for f in filas]


class RepositorioDocumentos(RepositorioBase):
    TABLA = "documentos"

    def _a_objeto(self, fila):
        return Documento(fila["codigo_item"], fila["profesional_id"], fila["periodo"],
                         fila["nombre_original"], fila["ruta_archivo"],
                         nino_id=fila["nino_id"], observaciones=fila["observaciones"],
                         fecha_carga=datetime.fromisoformat(fila["fecha_carga"]),
                         id_=fila["id"])

    def guardar(self, doc):
        doc.id = self._bd.ejecutar(
            "INSERT INTO documentos (codigo_item, profesional_id, nino_id, periodo, "
            "nombre_original, ruta_archivo, observaciones, fecha_carga) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (doc.codigo_item, doc.profesional_id, doc.nino_id, doc.periodo,
             doc.nombre_original, doc.ruta_archivo, doc.observaciones,
             doc.fecha_carga.isoformat()))
        return doc

    def por_item(self, profesional_id, codigo_item, periodo=None):
        sql = "SELECT * FROM documentos WHERE profesional_id = ? AND codigo_item = ?"
        params = [profesional_id, codigo_item]
        if periodo:
            sql += " AND periodo = ?"
            params.append(periodo)
        sql += " ORDER BY fecha_carga DESC"
        return [self._a_objeto(f) for f in self._bd.consultar(sql, params)]

    def existe_documento_unico(self, codigo_item, nino_id):
        fila = self._bd.consultar_uno(
            "SELECT 1 FROM documentos WHERE codigo_item = ? AND nino_id IS ?",
            (codigo_item, nino_id))
        return fila is not None

    def conteo_por_item(self, profesional_id, periodo):
        """Una sola consulta agrupada para el panel del profesional.

        Devuelve {codigo_item: (documentos_del_periodo, ninos_distintos_del_periodo,
                                documentos_historicos, ninos_distintos_historicos)}.
        """
        filas = self._bd.consultar(
            """
            SELECT codigo_item,
                   SUM(CASE WHEN periodo = :p THEN 1 ELSE 0 END)              AS docs_periodo,
                   COUNT(DISTINCT CASE WHEN periodo = :p THEN nino_id END)    AS ninos_periodo,
                   COUNT(*)                                                    AS docs_total,
                   COUNT(DISTINCT nino_id)                                     AS ninos_total
            FROM documentos
            WHERE profesional_id = :prof
            GROUP BY codigo_item
            """, {"p": periodo, "prof": profesional_id})
        return {f["codigo_item"]: (f["docs_periodo"], f["ninos_periodo"],
                                   f["docs_total"], f["ninos_total"]) for f in filas}


class RepositorioBitacora(RepositorioBase):
    TABLA = "bitacora"

    def _a_objeto(self, fila):
        return dict(fila)

    def registrar(self, fecha, usuario, tipo, detalle):
        return self._bd.ejecutar(
            "INSERT INTO bitacora (fecha, usuario, tipo, detalle) VALUES (?, ?, ?, ?)",
            (fecha.isoformat(sep=" "), usuario, tipo, detalle))

    def ultimos(self, cantidad=50):
        filas = self._bd.consultar(
            "SELECT * FROM bitacora ORDER BY id DESC LIMIT ?", (cantidad,))
        return [self._a_objeto(f) for f in filas]
