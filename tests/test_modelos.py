import unittest
from datetime import date

from cdi.modelos import (Alcance, Coordinador, Documento, ItemDocumental, Nino,
                         Nutricionista, Pedagogo, Profesional, Psicologo,
                         TrabajadorSocial)


class TestItemDocumental(unittest.TestCase):
    def test_acepta_solo_extensiones_permitidas(self):
        item = ItemDocumental("X", "Prueba", "", extensiones=(".pdf",))
        self.assertTrue(item.acepta_archivo("acta.PDF"))
        self.assertFalse(item.acepta_archivo("foto.png"))

    def test_atributos_son_de_solo_lectura(self):
        item = ItemDocumental("X", "Prueba", "")
        with self.assertRaises(AttributeError):
            item.codigo = "Y"

    def test_requiere_codigo(self):
        with self.assertRaises(ValueError):
            ItemDocumental("", "Sin código", "")


class TestProfesionales(unittest.TestCase):
    def setUp(self):
        self.nutri = Nutricionista("123", "Valentina", "valentina", clave="clave123")

    def test_no_se_puede_instanciar_la_clase_abstracta(self):
        with self.assertRaises(TypeError):
            Profesional("1", "X", "x", clave="123456")

    def test_items_de_la_nutricionista(self):
        titulos = [i.titulo for i in self.nutri.items_documentales()]
        self.assertIn("Entrega de Bienestarina", titulos)
        self.assertIn("Carné de vacunación", titulos)
        self.assertIn("Datos antropométricos", titulos)
        self.assertEqual(len(titulos), 5)

    def test_polimorfismo_items_distintos_por_profesional(self):
        clases = [Nutricionista, Psicologo, Pedagogo, TrabajadorSocial, Coordinador]
        codigos = set()
        for clase in clases:
            p = clase("1", "Persona", clase.TIPO, clave="123456")
            for item in p.items_documentales():
                codigos.add(item.codigo)
            self.assertTrue(p.descripcion_rol())
        # ningún código se repite entre profesionales
        total = sum(len(c("1", "P", "u", clave="123456").items_documentales()) for c in clases)
        self.assertEqual(len(codigos), total)

    def test_solo_el_coordinador_ve_reportes(self):
        coord = Coordinador("9", "Ana", "ana", clave="123456")
        self.assertTrue(coord.puede_ver_reportes())
        self.assertFalse(self.nutri.puede_ver_reportes())

    def test_clave_se_guarda_cifrada(self):
        self.assertNotEqual(self.nutri.clave_hash, "clave123")
        self.assertTrue(self.nutri.verificar_clave("clave123"))
        self.assertFalse(self.nutri.verificar_clave("otra"))

    def test_cambiar_clave(self):
        with self.assertRaises(PermissionError):
            self.nutri.cambiar_clave("mala", "nueva123")
        self.nutri.cambiar_clave("clave123", "nueva123")
        self.assertTrue(self.nutri.verificar_clave("nueva123"))

    def test_buscar_item(self):
        self.assertEqual(self.nutri.buscar_item("NUT-VAC").alcance, Alcance.POR_NINO)
        self.assertIsNone(self.nutri.buscar_item("PSI-VAL"))


class TestNinoYDocumento(unittest.TestCase):
    def test_edad_en_meses(self):
        nino = Nino("1001", "Sofía", date(2023, 3, 15), "María")
        self.assertEqual(nino.edad_en_meses(hoy=date(2024, 3, 14)), 11)
        self.assertEqual(nino.edad_en_meses(hoy=date(2024, 3, 15)), 12)

    def test_fecha_futura_no_valida(self):
        with self.assertRaises(ValueError):
            Nino("1", "X", date(2999, 1, 1), "Y")

    def test_periodo_invalido(self):
        with self.assertRaises(ValueError):
            Documento("NUT-BIEN", 1, "2026-13", "a.pdf", "ruta")
        doc = Documento("NUT-BIEN", 1, "2026-11", "a.pdf", "ruta")
        self.assertEqual(doc.periodo, "2026-11")


if __name__ == "__main__":
    unittest.main()
