"""Aplicación web (Flask). Solo maneja peticiones y pantallas;
toda la lógica está en las capas de modelos y servicios."""

import os
from datetime import date
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   send_file, session, url_for)

from cdi.modelos import Nino
from cdi.persistencia import (RepositorioBitacora, RepositorioNinos,
                              RepositorioProfesionales, inicializar_bd)
from cdi.servicios import (BitacoraAuditoria, ErrorDocumento, GestorDocumental,
                           NotificadorPantalla, ReporteCumplimiento)

from .datos_demo import cargar_datos_demo

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def periodo_actual():
    hoy = date.today()
    return f"{hoy.year}-{hoy.month:02d}"


def nombre_periodo(periodo):
    anio, mes = periodo.split("-")
    return f"{MESES[int(mes) - 1]} {anio}"


def ultimos_periodos(cantidad=12):
    hoy = date.today()
    anio, mes = hoy.year, hoy.month
    periodos = []
    for _ in range(cantidad):
        periodos.append(f"{anio}-{mes:02d}")
        mes -= 1
        if mes == 0:
            anio, mes = anio - 1, 12
    return periodos


def crear_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.environ.get("CDI_SECRET_KEY", "cambiar-esta-clave-en-produccion"),
        RUTA_BD=os.path.join(app.instance_path, "cdi.db"),
        CARPETA_ARCHIVOS=os.path.join(app.instance_path, "uploads"),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        CARGAR_DEMO=True,
    )
    if config:
        app.config.update(config)
    os.makedirs(app.instance_path, exist_ok=True)

    # --- Armado de dependencias ---
    inicializar_bd(app.config["RUTA_BD"])
    if app.config["CARGAR_DEMO"]:
        cargar_datos_demo()

    gestor = GestorDocumental(app.config["CARPETA_ARCHIVOS"])
    notificador = NotificadorPantalla()
    gestor.suscribir(BitacoraAuditoria())
    gestor.suscribir(notificador)
    reporte = ReporteCumplimiento(gestor)
    repo_prof = RepositorioProfesionales()
    repo_ninos = RepositorioNinos()

    app.extensions["gestor"] = gestor   # disponible para las pruebas

    # --- Utilidades ---
    @app.before_request
    def cargar_usuario():
        uid = session.get("uid")
        g.usuario = repo_prof.obtener(uid) if uid else None

    @app.context_processor
    def variables_globales():
        return {"usuario": g.get("usuario"), "nombre_periodo": nombre_periodo}

    def requiere_login(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if g.usuario is None:
                return redirect(url_for("login", siguiente=request.path))
            return vista(*args, **kwargs)
        return envoltura

    def requiere_coordinacion(vista):
        @wraps(vista)
        @requiere_login
        def envoltura(*args, **kwargs):
            if not g.usuario.puede_ver_reportes():
                abort(403)
            return vista(*args, **kwargs)
        return envoltura

    def pasar_notificaciones():
        for mensaje in notificador.tomar_mensajes(g.usuario.usuario):
            flash(mensaje, "ok")

    def periodo_solicitado():
        periodo = request.values.get("periodo", periodo_actual())
        return periodo if periodo in ultimos_periodos(24) else periodo_actual()

    # --- Rutas ---
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            p = repo_prof.buscar_por_usuario(request.form.get("usuario"))
            if p and p.verificar_clave(request.form.get("clave", "")):
                session.clear()
                session["uid"] = p.id
                siguiente = request.args.get("siguiente", "")
                return redirect(siguiente if siguiente.startswith("/") else url_for("panel"))
            flash("Usuario o clave incorrectos", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    @requiere_login
    def panel():
        periodo = periodo_solicitado()
        estados = gestor.estado_items(g.usuario, periodo)
        completos = sum(1 for e in estados if e.completo)
        return render_template("panel.html", estados=estados, periodo=periodo,
                               periodos=ultimos_periodos(), completos=completos)

    @app.route("/item/<codigo>")
    @requiere_login
    def ver_item(codigo):
        item = g.usuario.buscar_item(codigo) or abort(404)
        periodo = periodo_solicitado()
        documentos = gestor.documentos_de_item(g.usuario, codigo,
                                               periodo if item.es_mensual else None)
        ninos = {n.id: n for n in repo_ninos.listar()}
        pendientes = gestor.ninos_pendientes(g.usuario, codigo, periodo)
        return render_template("item.html", item=item, periodo=periodo,
                               periodos=ultimos_periodos(), documentos=documentos,
                               ninos=ninos, pendientes=pendientes)

    @app.route("/item/<codigo>/subir", methods=["POST"])
    @requiere_login
    def subir(codigo):
        periodo = periodo_solicitado()
        archivo = request.files.get("archivo")
        try:
            gestor.subir_documento(
                g.usuario, codigo, archivo, archivo.filename if archivo else "",
                periodo, nino_id=request.form.get("nino_id", type=int),
                observaciones=request.form.get("observaciones", ""))
            pasar_notificaciones()
        except ErrorDocumento as e:
            flash(str(e), "error")
        return redirect(url_for("ver_item", codigo=codigo, periodo=periodo))

    @app.route("/documento/<int:doc_id>/descargar")
    @requiere_login
    def descargar(doc_id):
        doc = gestor.obtener_documento(doc_id) or abort(404)
        if doc.profesional_id != g.usuario.id and not g.usuario.puede_ver_reportes():
            abort(403)
        return send_file(gestor.ruta_absoluta(doc), as_attachment=True,
                         download_name=doc.nombre_original)

    @app.route("/documento/<int:doc_id>/eliminar", methods=["POST"])
    @requiere_login
    def eliminar(doc_id):
        doc = gestor.obtener_documento(doc_id) or abort(404)
        try:
            gestor.eliminar_documento(g.usuario, doc_id)
            pasar_notificaciones()
        except PermissionError as e:
            flash(str(e), "error")
        return redirect(url_for("ver_item", codigo=doc.codigo_item, periodo=doc.periodo))

    @app.route("/ninos", methods=["GET", "POST"])
    @requiere_login
    def ninos():
        if request.method == "POST":
            f = request.form
            try:
                nino = Nino(f.get("documento"), f.get("nombres", ""),
                            f.get("fecha_nacimiento", ""), f.get("acudiente", ""),
                            f.get("telefono", ""))
                repo_ninos.guardar(nino)
                flash(f"Niño registrado: {nino.nombres}", "ok")
                return redirect(url_for("ninos"))
            except ValueError as e:
                flash(f"No se pudo registrar: {e}", "error")
        return render_template("ninos.html", ninos=repo_ninos.listar(), hoy=date.today())

    @app.route("/reporte")
    @requiere_coordinacion
    def ver_reporte():
        periodo = periodo_solicitado()
        filas = reporte.generar(g.usuario, periodo)
        return render_template("reporte.html", filas=filas, periodo=periodo,
                               periodos=ultimos_periodos(),
                               promedio=ReporteCumplimiento.promedio_general(filas))

    @app.route("/bitacora")
    @requiere_coordinacion
    def ver_bitacora():
        return render_template("bitacora.html", registros=RepositorioBitacora().ultimos(100))

    @app.errorhandler(403)
    def prohibido(_):
        return render_template("error.html", mensaje="No tiene permiso para ver esta página."), 403

    @app.errorhandler(404)
    def no_encontrado(_):
        return render_template("error.html", mensaje="La página no existe."), 404

    @app.errorhandler(413)
    def muy_grande(_):
        flash("El archivo supera el tamaño máximo de 10 MB", "error")
        return redirect(request.referrer or url_for("panel"))

    return app
