"""Patrón Singleton: una única conexión a la base de datos en toda la app.

Así todos los repositorios comparten la misma conexión SQLite y no se
abren conexiones nuevas en cada consulta.
"""

import sqlite3
import threading


class ConexionBD:
    _instancia = None
    _candado = threading.Lock()

    def __new__(cls, ruta="cdi.db"):
        # Doble verificación para que sea seguro con varios hilos (Flask)
        if cls._instancia is None:
            with cls._candado:
                if cls._instancia is None:
                    instancia = super().__new__(cls)
                    instancia._iniciar(ruta)
                    cls._instancia = instancia
        return cls._instancia

    def _iniciar(self, ruta):
        self.__ruta = ruta
        self.__conexion = sqlite3.connect(ruta, check_same_thread=False)
        self.__conexion.row_factory = sqlite3.Row
        self.__conexion.execute("PRAGMA foreign_keys = ON")
        self.__bloqueo_escritura = threading.Lock()

    @property
    def ruta(self):
        return self.__ruta

    def consultar(self, sql, parametros=()):
        """Ejecuta un SELECT y devuelve todas las filas."""
        return self.__conexion.execute(sql, parametros).fetchall()

    def consultar_uno(self, sql, parametros=()):
        return self.__conexion.execute(sql, parametros).fetchone()

    def ejecutar(self, sql, parametros=()):
        """Ejecuta INSERT/UPDATE/DELETE y devuelve el id insertado."""
        with self.__bloqueo_escritura:
            cursor = self.__conexion.execute(sql, parametros)
            self.__conexion.commit()
            return cursor.lastrowid

    def ejecutar_script(self, script):
        with self.__bloqueo_escritura:
            self.__conexion.executescript(script)
            self.__conexion.commit()

    def ejecutar_muchos(self, sql, filas):
        with self.__bloqueo_escritura:
            self.__conexion.executemany(sql, filas)
            self.__conexion.commit()

    @classmethod
    def reiniciar(cls):
        """Cierra la conexión actual (se usa en las pruebas)."""
        with cls._candado:
            if cls._instancia is not None:
                cls._instancia.__conexion.close()
                cls._instancia = None
