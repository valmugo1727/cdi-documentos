import threading
import unittest

from cdi.modelos import Coordinador, Nutricionista
from cdi.patrones import ConexionBD, Evento, FabricaProfesional, Observador, Sujeto


class TestSingleton(unittest.TestCase):
    def setUp(self):
        ConexionBD.reiniciar()

    def tearDown(self):
        ConexionBD.reiniciar()

    def test_siempre_es_la_misma_instancia(self):
        a = ConexionBD(":memory:")
        b = ConexionBD("otra_ruta.db")   # se ignora: ya existe la instancia
        self.assertIs(a, b)
        self.assertEqual(b.ruta, ":memory:")

    def test_misma_instancia_con_varios_hilos(self):
        instancias = []

        def crear():
            instancias.append(ConexionBD(":memory:"))

        hilos = [threading.Thread(target=crear) for _ in range(20)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        self.assertEqual(len({id(i) for i in instancias}), 1)


class TestFactoryMethod(unittest.TestCase):
    def test_crea_la_subclase_correcta(self):
        p = FabricaProfesional.para("nutricionista").crear(
            identificacion="1", nombres="Valentina", usuario="vale", clave="123456")
        self.assertIsInstance(p, Nutricionista)
        c = FabricaProfesional.para("coordinador").crear(
            identificacion="2", nombres="Ana", usuario="ana", clave="123456")
        self.assertIsInstance(c, Coordinador)

    def test_tipo_desconocido(self):
        with self.assertRaises(ValueError):
            FabricaProfesional.para("astronauta")

    def test_todas_las_fabricas_registradas(self):
        self.assertEqual(
            FabricaProfesional.tipos_disponibles(),
            ["coordinador", "nutricionista", "pedagogo", "psicologo", "trabajador_social"])


class ObservadorDePrueba(Observador):
    def __init__(self):
        self.recibidos = []

    def actualizar(self, evento):
        self.recibidos.append(evento)


class TestObserver(unittest.TestCase):
    def test_notifica_a_todos_los_suscritos(self):
        sujeto = Sujeto()
        o1, o2 = ObservadorDePrueba(), ObservadorDePrueba()
        sujeto.suscribir(o1)
        sujeto.suscribir(o2)
        sujeto.suscribir(o1)           # no se duplica
        sujeto.notificar(Evento("prueba", "vale", "hola"))
        self.assertEqual(len(o1.recibidos), 1)
        self.assertEqual(len(o2.recibidos), 1)

    def test_desuscribir(self):
        sujeto = Sujeto()
        o = ObservadorDePrueba()
        sujeto.suscribir(o)
        sujeto.desuscribir(o)
        sujeto.notificar(Evento("prueba", "vale", "hola"))
        self.assertEqual(o.recibidos, [])

    def test_solo_acepta_observadores(self):
        with self.assertRaises(TypeError):
            Sujeto().suscribir("no soy observador")


if __name__ == "__main__":
    unittest.main()
