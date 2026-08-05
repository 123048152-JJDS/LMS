"""
LMS UPQ - Bootstrap de base de datos
=====================================

Este módulo se ejecuta automáticamente al arrancar la aplicación
(ver app.py -> create_app()). Es completamente IDEMPOTENTE:

  1. Si el esquema (tablas) todavía NO existe -> lo crea por completo
     (tipos ENUM, tablas, índices, triggers) y siembra los roles base
     y la oferta académica de la UPQ.
     Si el esquema YA existe -> no hace nada de esto (no se vuelve a
     ejecutar).

  2. Siempre revisa si ya existe un usuario ADMINISTRADOR:
       - Si ya existe -> no hace nada más.
       - Si no existe -> lo crea usando los datos definidos en el
         archivo .env (ADMIN_NOMBRE, ADMIN_APELLIDO_PATERNO,
         ADMIN_APELLIDO_MATERNO, ADMIN_CORREO, ADMIN_PASSWORD).

No depende de scripts externos (.sql / .sh): todo vive en este
archivo para poder invocarse directamente desde app.py.
"""

import os

from werkzeug.security import generate_password_hash


# ------------------------------------------------------------
# DDL completo del esquema (equivalente a postgresql/01_schema.sql,
# sin BEGIN/COMMIT porque la transacción se maneja aquí mismo).
# ------------------------------------------------------------
SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN
    CREATE TYPE estado_inscripcion AS ENUM ('ACTIVO', 'BAJA', 'FINALIZADO');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE estado_material AS ENUM ('BORRADOR', 'PUBLICADO', 'ARCHIVADO');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE alcance_material AS ENUM ('TODA_LA_CLASE', 'ALUMNOS_SELECCIONADOS');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE tipo_recurso AS ENUM ('PDF', 'IMAGEN', 'VIDEO', 'AUDIO', 'DOCUMENTO', 'PRESENTACION', 'ENLACE');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE OR REPLACE FUNCTION set_actualizado_en()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS roles (
    id              SMALLSERIAL PRIMARY KEY,
    nombre          VARCHAR(30) NOT NULL UNIQUE,
    descripcion     VARCHAR(150),
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carreras (
    id              SERIAL PRIMARY KEY,
    clave           VARCHAR(20) NOT NULL UNIQUE,
    nombre          VARCHAR(150) NOT NULL,
    activa          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW()
);

DO $$ BEGIN
    CREATE TRIGGER trg_carreras_actualizado_en
        BEFORE UPDATE ON carreras
        FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS periodos_academicos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(80) NOT NULL UNIQUE,
    fecha_inicio    DATE NOT NULL,
    fecha_fin       DATE NOT NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_periodo_fechas CHECK (fecha_fin >= fecha_inicio)
);

DO $$ BEGIN
    CREATE TRIGGER trg_periodos_actualizado_en
        BEFORE UPDATE ON periodos_academicos
        FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS usuarios (
    id                  BIGSERIAL PRIMARY KEY,
    rol_id              SMALLINT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    nombre              VARCHAR(80) NOT NULL,
    apellido_paterno    VARCHAR(80) NOT NULL,
    apellido_materno    VARCHAR(80),
    correo              VARCHAR(150) NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_acceso       TIMESTAMP,
    creado_en           TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios (rol_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios (activo);
CREATE INDEX IF NOT EXISTS idx_usuarios_nombre ON usuarios (apellido_paterno, apellido_materno, nombre);

DO $$ BEGIN
    CREATE TRIGGER trg_usuarios_actualizado_en
        BEFORE UPDATE ON usuarios
        FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS alumnos (
    id              BIGSERIAL PRIMARY KEY,
    usuario_id      BIGINT NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE ON UPDATE CASCADE,
    carrera_id      INTEGER NOT NULL REFERENCES carreras(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    matricula       VARCHAR(30) NOT NULL UNIQUE,
    cuatrimestre    SMALLINT NOT NULL,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_alumnos_cuatrimestre CHECK (cuatrimestre BETWEEN 1 AND 12)
);

CREATE INDEX IF NOT EXISTS idx_alumnos_carrera ON alumnos (carrera_id);

DO $$ BEGIN
    CREATE TRIGGER trg_alumnos_actualizado_en
        BEFORE UPDATE ON alumnos
        FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS profesores (
    id                  BIGSERIAL PRIMARY KEY,
    usuario_id          BIGINT NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE ON UPDATE CASCADE,
    numero_empleado     VARCHAR(30) NOT NULL UNIQUE,
    especialidad        VARCHAR(150),
    creado_en           TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en      TIMESTAMP NOT NULL DEFAULT NOW()
);

DO $$ BEGIN
    CREATE TRIGGER trg_profesores_actualizado_en
        BEFORE UPDATE ON profesores
        FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS materias (
    id              BIGSERIAL PRIMARY KEY,
    clave           VARCHAR(30) NOT NULL UNIQUE,
    nombre          VARCHAR(150) NOT NULL,
    descripcion     TEXT,
    activa          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_materias_nombre ON materias (nombre);
CREATE INDEX IF NOT EXISTS idx_materias_activa ON materias (activa);

DO $$ BEGIN
    CREATE TRIGGER trg_materias_actualizado_en
        BEFORE UPDATE ON materias
        FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS clases (
    id              BIGSERIAL PRIMARY KEY,
    materia_id      BIGINT NOT NULL REFERENCES materias(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    periodo_id      INTEGER NOT NULL REFERENCES periodos_academicos(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    codigo_clase    VARCHAR(30) NOT NULL UNIQUE,
    nombre_grupo    VARCHAR(50) NOT NULL,
    descripcion     TEXT,
    activa          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_clase_materia_periodo_grupo UNIQUE (materia_id, periodo_id, nombre_grupo)
);

CREATE INDEX IF NOT EXISTS idx_clases_materia ON clases (materia_id);
CREATE INDEX IF NOT EXISTS idx_clases_periodo ON clases (periodo_id);
CREATE INDEX IF NOT EXISTS idx_clases_activa ON clases (activa);

DO $$ BEGIN
    CREATE TRIGGER trg_clases_actualizado_en
        BEFORE UPDATE ON clases
        FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS clase_profesores (
    clase_id        BIGINT NOT NULL REFERENCES clases(id) ON DELETE CASCADE ON UPDATE CASCADE,
    profesor_id     BIGINT NOT NULL REFERENCES profesores(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    es_titular      BOOLEAN NOT NULL DEFAULT TRUE,
    asignado_en     TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (clase_id, profesor_id)
);

CREATE INDEX IF NOT EXISTS idx_clase_profesores_profesor ON clase_profesores (profesor_id);

CREATE TABLE IF NOT EXISTS unidades (
    id              BIGSERIAL PRIMARY KEY,
    clase_id        BIGINT NOT NULL REFERENCES clases(id) ON DELETE CASCADE ON UPDATE CASCADE,
    titulo          VARCHAR(200) NOT NULL,
    descripcion     TEXT,
    orden           INTEGER NOT NULL DEFAULT 1,
    activa          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_unidades_clase ON unidades (clase_id);
CREATE INDEX IF NOT EXISTS idx_unidades_orden ON unidades (clase_id, orden);

DO $$ BEGIN
    CREATE TRIGGER trg_unidades_actualizado_en
        BEFORE UPDATE ON unidades
        FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS inscripciones (
    id              BIGSERIAL PRIMARY KEY,
    clase_id        BIGINT NOT NULL REFERENCES clases(id) ON DELETE CASCADE ON UPDATE CASCADE,
    alumno_id       BIGINT NOT NULL REFERENCES alumnos(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    estado          estado_inscripcion NOT NULL DEFAULT 'ACTIVO',
    inscrito_en     TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_inscripcion_clase_alumno UNIQUE (clase_id, alumno_id)
);

CREATE INDEX IF NOT EXISTS idx_inscripciones_alumno ON inscripciones (alumno_id);
CREATE INDEX IF NOT EXISTS idx_inscripciones_estado ON inscripciones (estado);

DO $$ BEGIN
    CREATE TRIGGER trg_inscripciones_actualizado_en
        BEFORE UPDATE ON inscripciones
        FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS materiales (
    id                          BIGSERIAL PRIMARY KEY,
    unidad_id                   BIGINT NOT NULL REFERENCES unidades(id) ON DELETE CASCADE ON UPDATE CASCADE,
    profesor_id                 BIGINT NOT NULL REFERENCES profesores(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    titulo                      VARCHAR(200) NOT NULL,
    descripcion_corta           VARCHAR(500),
    introduccion                TEXT NOT NULL,
    objetivo                    TEXT NOT NULL,
    metodologia_trabajo         TEXT NOT NULL,
    detalles_material           TEXT NOT NULL,
    referencias_bibliograficas  TEXT NOT NULL,
    conclusion                  TEXT NOT NULL,
    portada_ruta                VARCHAR(500),
    estado                      estado_material NOT NULL DEFAULT 'BORRADOR',
    alcance                     alcance_material NOT NULL DEFAULT 'TODA_LA_CLASE',
    permite_descarga            BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_publicacion           TIMESTAMP,
    activo                      BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en                   TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en              TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_materiales_unidad ON materiales (unidad_id);
CREATE INDEX IF NOT EXISTS idx_materiales_profesor ON materiales (profesor_id);
CREATE INDEX IF NOT EXISTS idx_materiales_estado ON materiales (estado);
CREATE INDEX IF NOT EXISTS idx_materiales_publicacion ON materiales (fecha_publicacion);
CREATE INDEX IF NOT EXISTS idx_materiales_activo ON materiales (activo);

DO $$ BEGIN
    CREATE TRIGGER trg_materiales_actualizado_en
        BEFORE UPDATE ON materiales
        FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS material_alumnos (
    material_id     BIGINT NOT NULL REFERENCES materiales(id) ON DELETE CASCADE ON UPDATE CASCADE,
    alumno_id       BIGINT NOT NULL REFERENCES alumnos(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    asignado_en     TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (material_id, alumno_id)
);

CREATE INDEX IF NOT EXISTS idx_material_alumnos_alumno ON material_alumnos (alumno_id);

CREATE TABLE IF NOT EXISTS material_colaboradores (
    material_id     BIGINT NOT NULL REFERENCES materiales(id) ON DELETE CASCADE ON UPDATE CASCADE,
    profesor_id     BIGINT NOT NULL REFERENCES profesores(id) ON DELETE CASCADE ON UPDATE CASCADE,
    autorizado_en   TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (material_id, profesor_id)
);

CREATE INDEX IF NOT EXISTS idx_material_colaboradores_profesor ON material_colaboradores (profesor_id);

CREATE TABLE IF NOT EXISTS recursos_material (
    id                  BIGSERIAL PRIMARY KEY,
    material_id         BIGINT NOT NULL REFERENCES materiales(id) ON DELETE CASCADE ON UPDATE CASCADE,
    tipo                tipo_recurso NOT NULL,
    nombre_original     VARCHAR(255) NOT NULL,
    ubicacion           VARCHAR(500) NOT NULL,
    mime_type           VARCHAR(120),
    tamanio_bytes       BIGINT,
    texto_alternativo   VARCHAR(300),
    descripcion         VARCHAR(500),
    orden               INTEGER NOT NULL DEFAULT 1,
    creado_en           TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recursos_material ON recursos_material (material_id);
CREATE INDEX IF NOT EXISTS idx_recursos_tipo ON recursos_material (tipo);
CREATE INDEX IF NOT EXISTS idx_recursos_orden ON recursos_material (material_id, orden);

CREATE TABLE IF NOT EXISTS consultas_material (
    id                  BIGSERIAL PRIMARY KEY,
    material_id         BIGINT NOT NULL REFERENCES materiales(id) ON DELETE CASCADE ON UPDATE CASCADE,
    alumno_id           BIGINT NOT NULL REFERENCES alumnos(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    primera_consulta    TIMESTAMP NOT NULL DEFAULT NOW(),
    ultima_consulta     TIMESTAMP NOT NULL DEFAULT NOW(),
    numero_consultas    INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT uq_consulta_material_alumno UNIQUE (material_id, alumno_id)
);

CREATE INDEX IF NOT EXISTS idx_consultas_alumno ON consultas_material (alumno_id);
CREATE INDEX IF NOT EXISTS idx_consultas_ultima ON consultas_material (ultima_consulta);
"""


# ------------------------------------------------------------
# Semillas: roles base y oferta académica de la UPQ.
# Con ON CONFLICT DO NOTHING son seguras de ejecutar siempre,
# pero solo se llaman la primera vez (cuando el esquema aún
# no existía) para no hacer trabajo de más en cada arranque.
# ------------------------------------------------------------
ROLES_SQL = """
INSERT INTO roles (nombre, descripcion) VALUES
    ('ADMINISTRADOR', 'Gestiona usuarios, materias, clases y asignaciones'),
    ('PROFESOR',       'Crea y publica materiales educativos'),
    ('ALUMNO',         'Consulta los materiales educativos asignados')
ON CONFLICT (nombre) DO NOTHING;
"""

CARRERAS_SQL = """
INSERT INTO carreras (clave, nombre, activa) VALUES
    ('IMECA',  'Ingeniería Mecatrónica', TRUE),
    ('ITAUTO', 'Ingeniería en Tecnología Automotriz', TRUE),
    ('ITIID',  'Ingeniería en Tecnologías de la Información e Innovación Digital', TRUE),
    ('ISC',    'Ingeniería en Sistemas Computacionales', TRUE),
    ('ITMA',   'Ingeniería en Tecnologías de Manufactura / Manufactura Avanzada', TRUE),
    ('IRT',    'Ingeniería en Redes y Telecomunicaciones', TRUE),
    ('IAD',    'Inteligencia Artificial y Datos', TRUE),
    ('LAGE',   'Administración y Gestión Empresarial / Administración', TRUE),
    ('LCIA',   'Comercio Internacional y Aduanas / Negocios Internacionales', TRUE)
ON CONFLICT (clave) DO NOTHING;
"""


def _esquema_existe(cursor):
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'usuarios'
        )
        """
    )
    return cursor.fetchone()[0]


def _obtener_administrador_existente(cursor):
    cursor.execute(
        """
        SELECT u.correo
        FROM usuarios u
        JOIN roles r ON r.id = u.rol_id
        WHERE r.nombre = 'ADMINISTRADOR'
        LIMIT 1
        """
    )
    return cursor.fetchone()


def _obtener_o_crear_rol_administrador(cursor):
    cursor.execute("SELECT id FROM roles WHERE nombre = 'ADMINISTRADOR'")
    fila = cursor.fetchone()

    if fila:
        return fila[0]

    cursor.execute(
        """
        INSERT INTO roles (nombre, descripcion)
        VALUES ('ADMINISTRADOR', 'Gestiona usuarios, materias, clases y asignaciones')
        RETURNING id
        """
    )
    return cursor.fetchone()[0]


def _crear_administrador_desde_env(cursor):
    """
    Lee los datos del administrador inicial desde las variables de
    entorno (ya cargadas por config.py a partir de .env) y lo crea.
    Si falta ADMIN_PASSWORD, no crea nada y solo avisa por consola
    (no se puede generar una contraseña seria por defecto).
    """
    correo = os.getenv("ADMIN_CORREO", "admin@upq.edu.mx").strip().lower()
    password = os.getenv("ADMIN_PASSWORD")

    if not password:
        print(
            "[bootstrap] No existe un administrador y no se definió "
            "ADMIN_PASSWORD en .env. No se creará ningún usuario. "
            "Agrega ADMIN_CORREO y ADMIN_PASSWORD a tu .env y reinicia "
            "la aplicación."
        )
        return

    nombre = os.getenv("ADMIN_NOMBRE", "Admin")
    apellido_paterno = os.getenv("ADMIN_APELLIDO_PATERNO", "UPQ")
    apellido_materno = os.getenv("ADMIN_APELLIDO_MATERNO", "Sistema")

    rol_id = _obtener_o_crear_rol_administrador(cursor)

    cursor.execute(
        """
        INSERT INTO usuarios (
            rol_id, nombre, apellido_paterno, apellido_materno,
            correo, password_hash, activo
        )
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        RETURNING correo
        """,
        (
            rol_id,
            nombre,
            apellido_paterno,
            apellido_materno,
            correo,
            generate_password_hash(password),
        ),
    )

    creado = cursor.fetchone()
    print(f"[bootstrap] Administrador creado correctamente: {creado[0]}")


def inicializar_base_datos(app, db):
    """
    Punto de entrada único. Llamar una vez desde create_app(),
    después de db.init_app(app).
    """
    with app.app_context():
        conexion = db.engine.raw_connection()

        try:
            cursor = conexion.cursor()

            if _esquema_existe(cursor):
                print("[bootstrap] El esquema ya existe. No se vuelve a crear.")
            else:
                print("[bootstrap] Esquema no encontrado. Creando base de datos desde cero...")
                cursor.execute(SCHEMA_SQL)
                cursor.execute(ROLES_SQL)
                cursor.execute(CARRERAS_SQL)
                conexion.commit()
                print("[bootstrap] Esquema, roles y oferta académica creados correctamente.")

            administrador = _obtener_administrador_existente(cursor)

            if administrador:
                print(
                    "[bootstrap] Ya existe un usuario administrador "
                    f"({administrador[0]}). No se realiza ninguna creación."
                )
            else:
                print("[bootstrap] No se encontró ningún administrador. Verificando datos en .env...")
                _crear_administrador_desde_env(cursor)
                conexion.commit()

        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()