import os
import shutil
import tempfile
import unittest
from datetime import date

from cdi.modelos import Coordinador, Nino, Nutricionista, Psicologo
from cdi.patrones import ConexionBD
from cdi.persistencia import (RepositorioBitacora, RepositorioNinos,
                              RepositorioProfesionales, inicializar_bd)
from cdi.servicios import (BitacoraAuditoria, ContadorEstadisticas, ErrorDocumento,
                           GestorDocumental, NotificadorPantalla, ReporteCumplimiento)

PERIODO = "2026-11"


class BaseServicio(unittest.TestCase):
    def setUp(self):
        ConexionBD.reiniciar()
        inicializar_bd(":memory:")
        self.carpeta = tempfile.mkdtemp()
        self.profesionales = RepositorioProfesionales()
        self.ninos = RepositorioNinos()
        self.nutri = self.profesionales.guardar(
            Nutricionista("111", "Valentina", "valentina", clave="clave123"))
        self.coord = self.profesionales.guardar(
            Coordinador("222", "Ana", "ana", clave="clave123"))
        self.nino1 = self.ninos.guardar(Nino("N1", "Sofía", date(2022, 5, 1), "María"))
        self.nino2 = self.ninos.guardar(Nino("N2", "Mateo", date(2021, 8, 9), "Luis"))
        self.gestor = GestorDocumental(self.carpeta)

    def tearDown(self):
        ConexionBD.reiniciar()
        shutil.rmtree(self.carpeta, ignore_errors=True)


class TestRepositorios(BaseServicio):
    def test_reconstruye_la_subclase_correcta(self):
        p = self.profesionales.buscar_por_usuario("VALENTINA")
        self.assertIsInstance(p, Nutricionista)
        self.assertTrue(p.verificar_clave("clave123"))

    def test_no_permite_ninos_duplicados(self):
        with self.assertRaises(ValueError):
            self.ninos.guardar(Nino("N1", "Otro", date(2022, 1, 1), "X"))

    def test_actualizar_clave(self):
        self.nutri.cambiar_clave("clave123", "nueva456")
        self.profesionales.guardar(self.nutri)
        p = self.profesionales.obtener(self.nutri.id)
        self.assertTrue(p.verificar_clave("nueva456"))


class TestGestorDocumental(BaseServicio):
    def test_subir_documento_general(self):
        doc = self.gestor.subir_documento(self.nutri, "NUT-BIEN", b"datos",
                                          "bienestarina.xlsx", PERIODO)
        self.assertIsNotNone(doc.id)
        self.assertTrue(os.path.exists(self.gestor.ruta_absoluta(doc)))

    def test_rechaza_item_de_otro_profesional(self):
        with self.assertRaises(ErrorDocumento):
            self.gestor.subir_documento(self.nutri, "PSI-VAL", b"x", "a.pdf", PERIODO)

    def test_rechaza_extension_no_permitida(self):
        with self.assertRaises(ErrorDocumento):
            self.gestor.subir_documento(self.nutri, "NUT-VAC", b"x", "virus.exe",
                                        PERIODO, nino_id=self.nino1.id)

    def test_item_por_nino_requiere_nino(self):
        with self.assertRaises(ErrorDocumento):
            self.gestor.subir_documento(self.nutri, "NUT-VAC", b"x", "carne.pdf", PERIODO)

    def test_documento_unico_no_se_repite(self):
        self.gestor.subir_documento(self.nutri, "NUT-VAC", b"x", "carne.pdf",
                                    PERIODO, nino_id=self.nino1.id)
        with self.assertRaises(ErrorDocumento):
            self.gestor.subir_documento(self.nutri, "NUT-VAC", b"x", "carne2.pdf",
                                        "2026-12", nino_id=self.nino1.id)

    def test_estado_de_items(self):
        self.gestor.subir_documento(self.nutri, "NUT-BIEN", b"x", "b.xlsx", PERIODO)
        self.gestor.subir_documento(self.nutri, "NUT-ANT", b"x", "a.xlsx",
                                    PERIODO, nino_id=self.nino1.id)
        estados = {e.item.codigo: e for e in self.gestor.estado_items(self.nutri, PERIODO)}
        self.assertTrue(estados["NUT-BIEN"].completo)
        self.assertEqual(estados["NUT-ANT"].porcentaje, 50)
        self.assertEqual(estados["NUT-ANT"].texto, "1 de 2 niños")
        self.assertFalse(estados["NUT-EDU"].completo)
        # en otro mes la bienestarina vuelve a estar pendiente
        otro = {e.item.codigo: e for e in self.gestor.estado_items(self.nutri, "2026-12")}
        self.assertFalse(otro["NUT-BIEN"].completo)

    def test_ninos_pendientes(self):
        self.gestor.subir_documento(self.nutri, "NUT-VAC", b"x", "c.pdf",
                                    PERIODO, nino_id=self.nino2.id)
        pendientes = self.gestor.ninos_pendientes(self.nutri, "NUT-VAC", PERIODO)
        self.assertEqual([n.nombres for n in pendientes], ["Sofía"])

    def test_eliminar_solo_el_dueno(self):
        doc = self.gestor.subir_documento(self.nutri, "NUT-BIEN", b"x", "b.xlsx", PERIODO)
        with self.assertRaises(PermissionError):
            self.gestor.eliminar_documento(self.coord, doc.id)
        self.gestor.eliminar_documento(self.nutri, doc.id)
        self.assertIsNone(self.gestor.obtener_documento(doc.id))


class TestObservadoresConcretos(BaseServicio):
    def test_bitacora_notificador_y_contador(self):
        notificador, contador = NotificadorPantalla(), ContadorEstadisticas()
        for o in (BitacoraAuditoria(), notificador, contador):
            self.gestor.suscribir(o)
        self.gestor.subir_documento(self.nutri, "NUT-BIEN", b"x", "b.xlsx", PERIODO)

        registros = RepositorioBitacora().ultimos()
        self.assertEqual(registros[0]["usuario"], "valentina")
        self.assertEqual(registros[0]["tipo"], "documento_subido")
        mensajes = notificador.tomar_mensajes("valentina")
        self.assertEqual(len(mensajes), 1)
        self.assertEqual(notificador.tomar_mensajes("valentina"), [])
        self.assertEqual(contador.total("documento_subido"), 1)


class TestReporte(BaseServicio):
    def test_solo_coordinador(self):
        reporte = ReporteCumplimiento(self.gestor)
        with self.assertRaises(PermissionError):
            reporte.generar(self.nutri, PERIODO)
        filas = reporte.generar(self.coord, PERIODO)
        self.assertEqual(len(filas), 2)
        self.assertEqual(ReporteCumplimiento.promedio_general(filas), 0)

    def test_porcentaje_sube_al_cargar(self):
        psico = self.profesionales.guardar(Psicologo("333", "Laura", "laura", clave="clave123"))
        for codigo in ("PSI-TAL", "PSI-REM", "PSI-NOV"):
            self.gestor.subir_documento(psico, codigo, b"x", "d.pdf", PERIODO)
        filas = {f.profesional.usuario: f for f in
                 ReporteCumplimiento(self.gestor).generar(self.coord, PERIODO)}
        # 3 ítems al 100 % y la valoración por niño al 0 % -> 75 %
        self.assertEqual(filas["laura"].porcentaje, 75)


if __name__ == "__main__":
    unittest.main()
