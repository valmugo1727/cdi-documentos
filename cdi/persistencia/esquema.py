"""Script de creación de tablas SQLite."""

ESQUEMA = """
CREATE TABLE IF NOT EXISTS profesionales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo            TEXT NOT NULL,
    identificacion  TEXT NOT NULL UNIQUE,
    nombres         TEXT NOT NULL,
    usuario         TEXT NOT NULL UNIQUE,
    clave_hash      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ninos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    documento           TEXT NOT NULL UNIQUE,
    nombres             TEXT NOT NULL,
    fecha_nacimiento    TEXT NOT NULL,
    acudiente           TEXT NOT NULL,
    telefono_acudiente  TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS documentos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_item      TEXT NOT NULL,
    profesional_id   INTEGER NOT NULL REFERENCES profesionales(id),
    nino_id          INTEGER REFERENCES ninos(id),
    periodo          TEXT NOT NULL,
    nombre_original  TEXT NOT NULL,
    ruta_archivo     TEXT NOT NULL,
    observaciones    TEXT DEFAULT '',
    fecha_carga      TEXT NOT NULL
);

-- Índices para que el panel y los reportes no recorran toda la tabla
CREATE INDEX IF NOT EXISTS idx_doc_prof_periodo ON documentos(profesional_id, periodo);
CREATE INDEX IF NOT EXISTS idx_doc_item_nino    ON documentos(codigo_item, nino_id);

CREATE TABLE IF NOT EXISTS bitacora (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha    TEXT NOT NULL,
    usuario  TEXT NOT NULL,
    tipo     TEXT NOT NULL,
    detalle  TEXT NOT NULL
);
"""
