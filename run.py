"""Punto de entrada. Ejecutar con:  python run.py
Luego abrir http://127.0.0.1:5000 en el navegador."""

from cdi.web import crear_app

app = crear_app()

if __name__ == "__main__":
    app.run(debug=True)
