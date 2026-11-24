"""Servicio principal: subir, consultar y eliminar documentos.

`GestorDocumental` hereda de `Sujeto` (patrón Observer): cada vez que
cambia algo, avisa a sus observadores.
"""

import os
import uuid
from dataclasses import dataclass

from werkzeug.utils import secure_filename

from cdi.modelos import Documento
from cdi.patrones import Evento, Sujeto
from cdi.persistencia import RepositorioDocumentos, RepositorioNinos

TAMANO_MAXIMO = 10 * 1024 * 1024   # 10 MB


class ErrorDocumento(Exception):
    """Error de validación al subir un documento."""


@dataclass
class EstadoItem:
    item: object
    cargados: int
    esperados: int

    @property
    def porcentaje(self):
        if self.esperados == 0:
            return 100
        return round(min(self.cargados / self.esperados, 1) * 100)

    @property
    def completo(self):
        return self.porcentaje == 100

    @property
    def texto(self):
        if self.item.es_por_nino:
            return f"{self.cargados} de {self.esperados} niños"
        return "Cargado" if self.completo else "Pendiente"


class GestorDocumental(Sujeto):
    def __init__(self, carpeta_archivos):
        super().__init__()
        self.__carpeta = carpeta_archivos
        self.__docs = RepositorioDocumentos()
        self.__ninos = RepositorioNinos()
        os.makedirs(self.__carpeta, exist_ok=True)

    @property
    def carpeta(self):
        return self.__carpeta

    # ------------------------------------------------------------------
    def subir_documento(self, profesional, codigo_item, archivo, nombre_archivo,
                        periodo, nino_id=None, observaciones=""):
        """Valida y guarda un documento. `archivo` puede ser bytes o un
        objeto con método save() (como el FileStorage de Flask)."""
        item = profesional.buscar_item(codigo_item)
        if item is None:
            raise ErrorDocumento("Este ítem no pertenece a su perfil profesional")
        if not nombre_archivo:
            raise ErrorDocumento("Debe seleccionar un archivo")
        if not item.acepta_archivo(nombre_archivo):
            raise ErrorDocumento(
                f"Formato no permitido. Use: {', '.join(item.extensiones)}")

        if item.es_por_nino:
            if not nino_id:
                raise ErrorDocumento("Este documento se carga por niño: seleccione uno")
            if self.__ninos.obtener(nino_id) is None:
                raise ErrorDocumento("El niño seleccionado no existe")
        else:
            nino_id = None

        if not item.es_mensual and self.__docs.existe_documento_unico(codigo_item, nino_id):
            raise ErrorDocumento("Este documento es de única vez y ya fue cargado")

        ruta = self.__guardar_archivo(profesional, codigo_item, periodo,
                                      archivo, nombre_archivo)
        doc = Documento(codigo_item, profesional.id, periodo, nombre_archivo, ruta,
                        nino_id=nino_id, observaciones=observaciones)
        try:
            self.__docs.guardar(doc)
        except Exception:
            os.remove(os.path.join(self.__carpeta, ruta))
            raise

        self.notificar(Evento("documento_subido", profesional.usuario,
                              f"{item.titulo} ({periodo}): {nombre_archivo}",
                              {"documento_id": doc.id, "item": codigo_item}))
        return doc

    def __guardar_archivo(self, profesional, codigo_item, periodo, archivo, nombre):
        subcarpeta = os.path.join(profesional.TIPO, codigo_item, periodo)
        os.makedirs(os.path.join(self.__carpeta, subcarpeta), exist_ok=True)
        nombre_seguro = f"{uuid.uuid4().hex[:8]}_{secure_filename(nombre) or 'archivo'}"
        relativa = os.path.join(subcarpeta, nombre_seguro)
        destino = os.path.join(self.__carpeta, relativa)
        if isinstance(archivo, (bytes, bytearray)):
            if len(archivo) > TAMANO_MAXIMO:
                raise ErrorDocumento("El archivo supera los 10 MB")
            with open(destino, "wb") as f:
                f.write(archivo)
        else:
            archivo.save(destino)
        return relativa

    # ------------------------------------------------------------------
    def eliminar_documento(self, profesional, documento_id):
        doc = self.__docs.obtener(documento_id)
        if doc is None:
            raise ErrorDocumento("El documento no existe")
        if doc.profesional_id != profesional.id:
            raise PermissionError("Solo quien cargó el documento puede eliminarlo")
        ruta = os.path.join(self.__carpeta, doc.ruta_archivo)
        if os.path.exists(ruta):
            os.remove(ruta)
        self.__docs.eliminar(documento_id)
        self.notificar(Evento("documento_eliminado", profesional.usuario,
                              f"{doc.codigo_item} ({doc.periodo}): {doc.nombre_original}"))

    def obtener_documento(self, documento_id):
        return self.__docs.obtener(documento_id)

    def ruta_absoluta(self, documento):
        return os.path.join(self.__carpeta, documento.ruta_archivo)

    def documentos_de_item(self, profesional, codigo_item, periodo=None):
        return self.__docs.por_item(profesional.id, codigo_item, periodo)

    # ------------------------------------------------------------------
    def estado_items(self, profesional, periodo):
        """Estado de cada ítem del profesional en el periodo indicado."""
        conteos = self.__docs.conteo_por_item(profesional.id, periodo)
        total_ninos = self.__ninos.contar()
        estados = []
        for item in profesional.items_documentales():
            docs_p, ninos_p, docs_t, ninos_t = conteos.get(item.codigo, (0, 0, 0, 0))
            if item.es_por_nino:
                cargados = ninos_p if item.es_mensual else ninos_t
                esperados = total_ninos
            else:
                cargados = docs_p if item.es_mensual else docs_t
                esperados = 1
            estados.append(EstadoItem(item, min(cargados, esperados) if esperados else cargados,
                                      esperados))
        return estados

    def ninos_pendientes(self, profesional, codigo_item, periodo):
        """Niños a los que aún les falta el documento en ese ítem."""
        item = profesional.buscar_item(codigo_item)
        if item is None or not item.es_por_nino:
            return []
        docs = self.__docs.por_item(profesional.id, codigo_item,
                                    periodo if item.es_mensual else None)
        con_documento = {d.nino_id for d in docs}
        return [n for n in self.__ninos.listar() if n.id not in con_documento]
