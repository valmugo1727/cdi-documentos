import io
import shutil
import tempfile
import unittest

from cdi.patrones import ConexionBD
from cdi.web import crear_app


class TestWeb(unittest.TestCase):
    def setUp(self):
        ConexionBD.reiniciar()
        self.carpeta = tempfile.mkdtemp()
        self.app = crear_app({"RUTA_BD": ":memory:", "CARPETA_ARCHIVOS": self.carpeta,
                              "TESTING": True})
        self.cliente = self.app.test_client()

    def tearDown(self):
        ConexionBD.reiniciar()
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def entrar(self, usuario):
        return self.cliente.post("/login", data={"usuario": usuario, "clave": "cdi2026"})

    def test_redirige_al_login_sin_sesion(self):
        r = self.cliente.get("/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.location)

    def test_clave_incorrecta(self):
        r = self.cliente.post("/login", data={"usuario": "nutricion", "clave": "mala"})
        self.assertIn("incorrectos", r.get_data(as_text=True))

    def test_panel_muestra_items_del_profesional(self):
        self.entrar("nutricion")
        html = self.cliente.get("/").get_data(as_text=True)
        self.assertIn("Entrega de Bienestarina", html)
        self.assertNotIn("Planeación pedagógica", html)

    def test_subir_y_descargar(self):
        self.entrar("nutricion")
        r = self.cliente.post("/item/NUT-BIEN/subir", data={
            "archivo": (io.BytesIO(b"contenido"), "bienestarina.xlsx"),
            "periodo": "2026-11"}, content_type="multipart/form-data",
            follow_redirects=True)
        self.assertIn("Documento cargado", r.get_data(as_text=True))
        r = self.cliente.get("/documento/1/descargar")
        self.assertEqual(r.data, b"contenido")
        r.close()

    def test_otro_profesional_no_descarga(self):
        self.entrar("nutricion")
        self.cliente.post("/item/NUT-BIEN/subir", data={
            "archivo": (io.BytesIO(b"x"), "b.xlsx"), "periodo": "2026-11"},
            content_type="multipart/form-data")
        self.cliente.get("/logout")
        self.entrar("psicologia")
        self.assertEqual(self.cliente.get("/documento/1/descargar").status_code, 403)

    def test_item_ajeno_da_404(self):
        self.entrar("psicologia")
        self.assertEqual(self.cliente.get("/item/NUT-BIEN").status_code, 404)

    def test_reporte_solo_coordinacion(self):
        self.entrar("nutricion")
        self.assertEqual(self.cliente.get("/reporte").status_code, 403)
        self.cliente.get("/logout")
        self.entrar("coordinacion")
        html = self.cliente.get("/reporte").get_data(as_text=True)
        self.assertIn("Valentina Rosero", html)

    def test_registrar_nino(self):
        self.entrar("pedagogia")
        r = self.cliente.post("/ninos", data={
            "documento": "999", "nombres": "Emilio Paz", "fecha_nacimiento": "2023-02-01",
            "acudiente": "Clara Paz"}, follow_redirects=True)
        self.assertIn("Emilio Paz", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
