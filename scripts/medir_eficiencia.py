"""Análisis de eficiencia del cálculo de estado del panel.

Compara dos formas de calcular el estado de los ítems de un profesional:
  A) Ingenua: una consulta por cada ítem y por cada niño  -> O(items x niños) consultas
  B) La usada en el proyecto: UNA consulta agrupada (GROUP BY) apoyada en índices.

Ejecutar desde la raíz del proyecto:  python scripts/medir_eficiencia.py
"""

import os
import random
import sys
import time
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cdi.modelos import Nino, Nutricionista            # noqa: E402
from cdi.patrones import ConexionBD                     # noqa: E402
from cdi.persistencia import (RepositorioNinos,         # noqa: E402
                              RepositorioProfesionales, inicializar_bd)
from cdi.servicios import GestorDocumental              # noqa: E402

PERIODO = "2026-11"


def poblar(n_ninos, docs_por_nino):
    ConexionBD.reiniciar()
    bd = inicializar_bd(":memory:")
    repo_prof = RepositorioProfesionales()
    # 5 profesionales para que la tabla tenga documentos de varias personas
    equipo = [repo_prof.guardar(Nutricionista(str(i), f"P{i}", f"p{i}", clave="123456"))
              for i in range(1, 6)]
    nutri = equipo[0]
    repo_ninos = RepositorioNinos()
    for i in range(n_ninos):
        repo_ninos.guardar(Nino(f"D{i}", f"Niño {i}", date(2022, 1, 1), "Acudiente"))
    items = [it.codigo for it in nutri.items_documentales()]
    filas = []
    for nino_id in range(1, n_ninos + 1):
        for _ in range(docs_por_nino):
            mes = random.randint(1, 11)
            filas.append((random.choice(items), random.choice(equipo).id, nino_id, f"2026-{mes:02d}",
                          "a.pdf", "ruta", "", "2026-11-01T00:00:00"))
    bd.ejecutar_muchos(
        "INSERT INTO documentos (codigo_item, profesional_id, nino_id, periodo, "
        "nombre_original, ruta_archivo, observaciones, fecha_carga) VALUES (?,?,?,?,?,?,?,?)",
        filas)
    return bd, nutri


def estado_ingenuo(bd, profesional, periodo):
    """Versión ingenua: una consulta por ítem y, si es por niño, una por cada niño."""
    ninos = bd.consultar("SELECT id FROM ninos")
    consultas = 1
    resultado = {}
    for item in profesional.items_documentales():
        if item.es_por_nino:
            cargados = 0
            for n in ninos:
                consultas += 1
                if bd.consultar_uno(
                        "SELECT 1 FROM documentos WHERE profesional_id=? AND codigo_item=? "
                        "AND nino_id=? AND (?=0 OR periodo=?)",
                        (profesional.id, item.codigo, n["id"], int(item.es_mensual), periodo)):
                    cargados += 1
        else:
            consultas += 1
            cargados = bd.consultar_uno(
                "SELECT COUNT(*) AS c FROM documentos WHERE profesional_id=? AND codigo_item=? "
                "AND (?=0 OR periodo=?)",
                (profesional.id, item.codigo, int(item.es_mensual), periodo))["c"]
        resultado[item.codigo] = cargados
    return resultado, consultas


def medir(funcion, repeticiones=5):
    inicio = time.perf_counter()
    for _ in range(repeticiones):
        funcion()
    return (time.perf_counter() - inicio) / repeticiones * 1000


def main():
    random.seed(7)
    latencia = 1.0   # ms por consulta si la BD estuviera en un servidor de red
    print(f"{'Niños':>6} {'Docs':>7} | {'Ingenuo':>9} {'Consultas':>9} {'Con red*':>9} | "
          f"{'Agrupado':>9} {'Sin índice':>10} {'Con red*':>9}")
    print("-" * 84)
    for n_ninos in (50, 200, 500, 1000):
        bd, nutri = poblar(n_ninos, docs_por_nino=50)
        gestor = GestorDocumental(os.path.join(os.path.dirname(__file__), "_tmp_archivos"))
        total_docs = bd.consultar_uno("SELECT COUNT(*) AS n FROM documentos")["n"]
        _, consultas_a = estado_ingenuo(bd, nutri, PERIODO)
        t_a = medir(lambda: estado_ingenuo(bd, nutri, PERIODO))
        t_b = medir(lambda: gestor.estado_items(nutri, PERIODO))
        bd.ejecutar("DROP INDEX idx_doc_prof_periodo")
        bd.ejecutar("DROP INDEX idx_doc_item_nino")
        t_c = medir(lambda: gestor.estado_items(nutri, PERIODO))
        print(f"{n_ninos:>6} {total_docs:>7} | {t_a:>9.1f} {consultas_a:>9} "
              f"{t_a + consultas_a * latencia:>9.0f} | {t_b:>9.1f} {t_c:>10.1f} "
              f"{t_b + 2 * latencia:>9.0f}")
    print("\nTiempos en milisegundos (promedio de 5 repeticiones).")
    print("* Estimación: tiempo medido + 1 ms por cada consulta, como pasaría con "
          "una base de datos en red.")
    ConexionBD.reiniciar()
    os.rmdir(os.path.join(os.path.dirname(__file__), "_tmp_archivos"))


if __name__ == "__main__":
    main()
