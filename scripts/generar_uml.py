"""Genera los diagramas UML del proyecto con Graphviz.

Requiere tener Graphviz instalado (comando `dot`):
  Windows: https://graphviz.org/download/   |   Linux: sudo apt install graphviz

Ejecutar desde la raíz:  python scripts/generar_uml.py
Crea docs/uml/diagrama_clases.(dot|png|svg) y docs/uml/diagrama_paquetes.(dot|png|svg)
"""

import os
import subprocess
from html import escape

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "docs", "uml")

COLORES = {
    "modelos": "#e3efed",
    "patrones": "#fbf0dc",
    "persistencia": "#e8e6f5",
    "servicios": "#e4f3ea",
    "web": "#f3e5e5",
}


def clase(nombre, atributos=(), metodos=(), estereotipo=None, abstracta=False, color="#ffffff"):
    """Devuelve la etiqueta HTML de Graphviz con las 3 secciones UML."""
    titulo = escape(nombre)
    if abstracta:
        titulo = f"<I>{titulo}</I>"
    cabecera = ""
    if estereotipo:
        cabecera = f'<FONT POINT-SIZE="9">«{escape(estereotipo)}»</FONT><BR/>'
    filas = [f'<TR><TD BGCOLOR="{color}"><B>{cabecera}{titulo}</B></TD></TR>']

    def bloque(lineas):
        if not lineas:
            return '<TR><TD> </TD></TR>'
        texto = '<BR ALIGN="LEFT"/>'.join(escape(l) for l in lineas)
        return f'<TR><TD ALIGN="LEFT" BALIGN="LEFT">{texto}<BR ALIGN="LEFT"/></TD></TR>'

    filas.append(bloque(atributos))
    filas.append(bloque(metodos))
    return ('<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
            + "".join(filas) + "</TABLE>>")


# ----------------------------------------------------------------------------
# Diagrama de clases
# ----------------------------------------------------------------------------
PAQUETES = {
    "modelos": {
        "Profesional": dict(
            abstracta=True, estereotipo="abstract",
            atributos=["- __id: int", "- __identificacion: str", "- __nombres: str",
                       "- __usuario: str", "- __clave_hash: str"],
            metodos=["+ verificar_clave(clave): bool", "+ cambiar_clave(actual, nueva)",
                     "+ buscar_item(codigo): ItemDocumental",
                     "+ puede_ver_reportes(): bool",
                     "+ items_documentales(): list {abstract}",
                     "+ descripcion_rol(): str {abstract}"]),
        "Nutricionista": dict(metodos=["+ items_documentales()", "+ descripcion_rol()"]),
        "Psicologo": dict(metodos=["+ items_documentales()", "+ descripcion_rol()"]),
        "Pedagogo": dict(metodos=["+ items_documentales()", "+ descripcion_rol()"]),
        "TrabajadorSocial": dict(metodos=["+ items_documentales()", "+ descripcion_rol()"]),
        "Coordinador": dict(metodos=["+ items_documentales()", "+ descripcion_rol()",
                                     "+ puede_ver_reportes(): bool"]),
        "ItemDocumental": dict(
            atributos=["- __codigo: str", "- __titulo: str", "- __descripcion: str",
                       "- __periodicidad: Periodicidad", "- __alcance: Alcance",
                       "- __extensiones: tuple"],
            metodos=["+ acepta_archivo(nombre): bool", "+ es_por_nino: bool",
                     "+ es_mensual: bool"]),
        "Periodicidad": dict(estereotipo="enumeration", atributos=["MENSUAL", "UNICA"]),
        "Alcance": dict(estereotipo="enumeration", atributos=["GENERAL", "POR_NINO"]),
        "Nino": dict(
            atributos=["- __id: int", "- __documento: str", "- __nombres: str",
                       "- __fecha_nacimiento: date", "- __acudiente: str"],
            metodos=["+ edad_en_meses(hoy): int"]),
        "Documento": dict(
            atributos=["- __id: int", "- __codigo_item: str", "- __profesional_id: int",
                       "- __nino_id: int", "- __periodo: str", "- __ruta_archivo: str",
                       "- __fecha_carga: datetime"]),
    },
    "patrones": {
        "ConexionBD": dict(
            estereotipo="Singleton",
            atributos=["- _instancia: ConexionBD {static}", "- _candado: Lock {static}"],
            metodos=["+ __new__(ruta): ConexionBD", "+ consultar(sql, params)",
                     "+ ejecutar(sql, params): int", "+ reiniciar() {static}"]),
        "FabricaProfesional": dict(
            abstracta=True, estereotipo="Factory Method",
            atributos=["- _registro: dict {static}"],
            metodos=["# _crear(**datos): Profesional {abstract}",
                     "+ crear(**datos): Profesional", "+ para(tipo): FabricaProfesional {static}"]),
        "FabricaNutricionista": dict(metodos=["# _crear(**datos)"]),
        "FabricaCoordinador": dict(metodos=["# _crear(**datos)"]),
        "Sujeto": dict(
            atributos=["- __observadores: list"],
            metodos=["+ suscribir(o: Observador)", "+ desuscribir(o)", "+ notificar(e: Evento)"]),
        "Observador": dict(abstracta=True, estereotipo="interface",
                           metodos=["+ actualizar(evento) {abstract}"]),
        "Evento": dict(atributos=["+ tipo: str", "+ usuario: str", "+ detalle: str",
                                  "+ fecha: datetime"]),
    },
    "persistencia": {
        "RepositorioBase": dict(
            abstracta=True, estereotipo="abstract",
            atributos=["# _bd: ConexionBD"],
            metodos=["# _a_objeto(fila) {abstract}", "+ obtener(id)", "+ listar(): list",
                     "+ contar(): int", "+ eliminar(id)"]),
        "RepositorioProfesionales": dict(metodos=["+ guardar(p)", "+ buscar_por_usuario(u)"]),
        "RepositorioNinos": dict(metodos=["+ guardar(n)", "+ buscar_por_documento(d)"]),
        "RepositorioDocumentos": dict(metodos=["+ guardar(d)", "+ por_item(...)",
                                               "+ conteo_por_item(prof, periodo): dict"]),
        "RepositorioBitacora": dict(metodos=["+ registrar(...)", "+ ultimos(n): list"]),
    },
    "servicios": {
        "GestorDocumental": dict(
            atributos=["- __carpeta: str", "- __docs: RepositorioDocumentos",
                       "- __ninos: RepositorioNinos"],
            metodos=["+ subir_documento(prof, item, archivo, ...): Documento",
                     "+ eliminar_documento(prof, id)",
                     "+ estado_items(prof, periodo): list[EstadoItem]",
                     "+ ninos_pendientes(prof, item, periodo): list"]),
        "EstadoItem": dict(atributos=["+ item: ItemDocumental", "+ cargados: int",
                                      "+ esperados: int"],
                           metodos=["+ porcentaje: int", "+ completo: bool"]),
        "ReporteCumplimiento": dict(metodos=["+ generar(solicitante, periodo): list",
                                             "+ promedio_general(filas) {static}"]),
        "BitacoraAuditoria": dict(metodos=["+ actualizar(evento)"]),
        "NotificadorPantalla": dict(metodos=["+ actualizar(evento)",
                                             "+ tomar_mensajes(usuario): list"]),
        "ContadorEstadisticas": dict(metodos=["+ actualizar(evento)", "+ total(tipo): int"]),
    },
    "web": {
        "app (Flask)": dict(estereotipo="module",
                            metodos=["+ crear_app(config): Flask",
                                     "rutas: /login, /, /item, /ninos,", "/reporte, /bitacora"]),
    },
}

TITULOS_PAQUETE = {
    "modelos": "cdi.modelos",
    "patrones": "cdi.patrones",
    "persistencia": "cdi.persistencia",
    "servicios": "cdi.servicios",
    "web": "cdi.web",
}

# (origen, destino, tipo, etiqueta)
#   herencia: origen hereda de destino
#   realiza:  origen implementa la interfaz destino
#   composicion: destino es parte de origen
#   asociacion / dependencia
RELACIONES = [
    ("Nutricionista", "Profesional", "herencia", ""),
    ("Psicologo", "Profesional", "herencia", ""),
    ("Pedagogo", "Profesional", "herencia", ""),
    ("TrabajadorSocial", "Profesional", "herencia", ""),
    ("Coordinador", "Profesional", "herencia", ""),
    ("Profesional", "ItemDocumental", "composicion", "1  ..  1..*"),
    ("ItemDocumental", "Periodicidad", "asociacion", ""),
    ("ItemDocumental", "Alcance", "asociacion", ""),
    ("Documento", "Profesional", "asociacion", "*  ..  1"),
    ("Documento", "Nino", "asociacion", "*  ..  0..1"),
    ("Documento", "ItemDocumental", "asociacion", "*  ..  1"),
    ("FabricaNutricionista", "FabricaProfesional", "herencia", ""),
    ("FabricaCoordinador", "FabricaProfesional", "herencia", ""),
    ("FabricaProfesional", "Profesional", "dependencia", "crea"),
    ("Sujeto", "Observador", "agregacion", "notifica  0..*"),
    ("Sujeto", "Evento", "dependencia", ""),
    ("RepositorioProfesionales", "RepositorioBase", "herencia", ""),
    ("RepositorioNinos", "RepositorioBase", "herencia", ""),
    ("RepositorioDocumentos", "RepositorioBase", "herencia", ""),
    ("RepositorioBitacora", "RepositorioBase", "herencia", ""),
    ("RepositorioBase", "ConexionBD", "asociacion", "usa"),
    ("RepositorioProfesionales", "FabricaProfesional", "dependencia", "reconstruye con"),
    ("GestorDocumental", "Sujeto", "herencia", ""),
    ("BitacoraAuditoria", "Observador", "realiza", ""),
    ("NotificadorPantalla", "Observador", "realiza", ""),
    ("ContadorEstadisticas", "Observador", "realiza", ""),
    ("BitacoraAuditoria", "RepositorioBitacora", "asociacion", ""),
    ("GestorDocumental", "RepositorioDocumentos", "composicion", ""),
    ("GestorDocumental", "RepositorioNinos", "composicion", ""),
    ("GestorDocumental", "EstadoItem", "dependencia", "produce"),
    ("ReporteCumplimiento", "GestorDocumental", "asociacion", ""),
    ("app (Flask)", "GestorDocumental", "asociacion", ""),
    ("app (Flask)", "ReporteCumplimiento", "asociacion", ""),
    ("app (Flask)", "NotificadorPantalla", "asociacion", ""),
]

ESTILO_RELACION = {
    "herencia": 'arrowhead=empty, style=solid',
    "realiza": 'arrowhead=empty, style=dashed',
    "composicion": 'dir=back, arrowtail=diamond, arrowhead=none',
    "agregacion": 'dir=back, arrowtail=odiamond, arrowhead=vee',
    "asociacion": 'arrowhead=vee',
    "dependencia": 'arrowhead=vee, style=dashed',
}


def nodo_id(nombre):
    return '"' + nombre + '"'


def diagrama_clases():
    lineas = [
        "digraph UML {",
        '  graph [rankdir=BT, splines=ortho, nodesep=0.35, ranksep=0.55, fontname="Helvetica",'
        ' label="Gestor Documental CDI — Diagrama de clases", labelloc=t, fontsize=18, pad=0.3];',
        '  node [shape=plain, fontname="Helvetica", fontsize=10];',
        '  edge [fontname="Helvetica", fontsize=9, color="#555555"];',
    ]
    for paquete, clases in PAQUETES.items():
        lineas.append(f"  subgraph cluster_{paquete} {{")
        lineas.append(f'    label="{TITULOS_PAQUETE[paquete]}"; style="rounded,dashed";'
                      ' color="#999999"; fontsize=12; margin=14;')
        for nombre, datos in clases.items():
            etiqueta = clase(nombre, color=COLORES[paquete], **datos)
            lineas.append(f"    {nodo_id(nombre)} [label={etiqueta}];")
        lineas.append("  }")
    for origen, destino, tipo, etiqueta in RELACIONES:
        extra = f', xlabel="{etiqueta}"' if etiqueta else ""
        lineas.append(f"  {nodo_id(origen)} -> {nodo_id(destino)} "
                      f"[{ESTILO_RELACION[tipo]}{extra}];")
    lineas.append("}")
    return "\n".join(lineas)


def diagrama_paquetes():
    return """digraph Paquetes {
  graph [rankdir=TB, fontname="Helvetica", label="Gestor Documental CDI — Arquitectura modular (capas)",
         labelloc=t, fontsize=16, nodesep=0.6, ranksep=0.6, pad=0.3];
  node [shape=folder, style=filled, fontname="Helvetica", fontsize=11, margin="0.25,0.12"];
  edge [arrowhead=vee, style=dashed, fontname="Helvetica", fontsize=9, color="#555555"];

  web [label="cdi.web\\n(Flask: rutas, plantillas, estilos)", fillcolor="%(web)s"];
  servicios [label="cdi.servicios\\n(GestorDocumental, observadores, reportes)", fillcolor="%(servicios)s"];
  persistencia [label="cdi.persistencia\\n(repositorios, esquema SQLite)", fillcolor="%(persistencia)s"];
  patrones [label="cdi.patrones\\n(Singleton, Factory Method, Observer)", fillcolor="%(patrones)s"];
  modelos [label="cdi.modelos\\n(Profesional, ItemDocumental, Nino, Documento)", fillcolor="%(modelos)s"];
  bd [label="SQLite\\n(instance/cdi.db)", shape=cylinder, fillcolor="#ffffff"];
  archivos [label="Archivos\\n(instance/uploads)", shape=cylinder, fillcolor="#ffffff"];

  web -> servicios [xlabel="usa"];
  web -> persistencia;
  servicios -> persistencia;
  servicios -> patrones;
  servicios -> modelos;
  persistencia -> patrones;
  persistencia -> modelos;
  patrones -> modelos;
  persistencia -> bd [style=solid];
  servicios -> archivos [style=solid];
  {rank=same; bd; archivos}
}
""" % COLORES


def escribir_y_renderizar(nombre, contenido):
    ruta_dot = os.path.join(SALIDA, nombre + ".dot")
    with open(ruta_dot, "w", encoding="utf-8") as f:
        f.write(contenido)
    for formato in ("png", "svg"):
        extra = ["-Gdpi=150"] if formato == "png" else []
        subprocess.run(["dot", f"-T{formato}", *extra, ruta_dot,
                        "-o", os.path.join(SALIDA, f"{nombre}.{formato}")], check=True)
    print("Generado:", nombre)


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    escribir_y_renderizar("diagrama_clases", diagrama_clases())
    escribir_y_renderizar("diagrama_paquetes", diagrama_paquetes())
