-- ============================================================
-- LMS UPQ - Esquema inicial para PostgreSQL
-- Convertido desde models.py (MySQL) a PostgreSQL
-- Ejecutar contra una base de datos vacía:
--   psql -U <usuario> -d lms_upq -f 01_schema.sql
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- Extensiones necesarias
-- ------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ------------------------------------------------------------
-- Tipos ENUM (equivalentes a los ENUM de MySQL en models.py)
-- ------------------------------------------------------------
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

-- ------------------------------------------------------------
-- Función utilitaria para actualizar automáticamente
-- la columna actualizado_en (equivalente a ON UPDATE
-- CURRENT_TIMESTAMP de MySQL, que Postgres no soporta nativo)
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_actualizado_en()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------
-- Tabla: roles
-- ------------------------------------------------------------
CREATE TABLE roles (
    id              SMALLSERIAL PRIMARY KEY,
    nombre          VARCHAR(30) NOT NULL UNIQUE,
    descripcion     VARCHAR(150),
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Tabla: carreras
-- ------------------------------------------------------------
CREATE TABLE carreras (
    id              SERIAL PRIMARY KEY,
    clave           VARCHAR(20) NOT NULL UNIQUE,
    nombre          VARCHAR(150) NOT NULL,
    activa          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_carreras_actualizado_en
    BEFORE UPDATE ON carreras
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();

-- ------------------------------------------------------------
-- Tabla: periodos_academicos
-- ------------------------------------------------------------
CREATE TABLE periodos_academicos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(80) NOT NULL UNIQUE,
    fecha_inicio    DATE NOT NULL,
    fecha_fin       DATE NOT NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_periodo_fechas CHECK (fecha_fin >= fecha_inicio)
);

CREATE TRIGGER trg_periodos_actualizado_en
    BEFORE UPDATE ON periodos_academicos
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();

-- ------------------------------------------------------------
-- Tabla: usuarios
-- ------------------------------------------------------------
CREATE TABLE usuarios (
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

CREATE INDEX idx_usuarios_rol ON usuarios (rol_id);
CREATE INDEX idx_usuarios_activo ON usuarios (activo);
CREATE INDEX idx_usuarios_nombre ON usuarios (apellido_paterno, apellido_materno, nombre);

CREATE TRIGGER trg_usuarios_actualizado_en
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();

-- ------------------------------------------------------------
-- Tabla: alumnos
-- ------------------------------------------------------------
CREATE TABLE alumnos (
    id              BIGSERIAL PRIMARY KEY,
    usuario_id      BIGINT NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE ON UPDATE CASCADE,
    carrera_id      INTEGER NOT NULL REFERENCES carreras(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    matricula       VARCHAR(30) NOT NULL UNIQUE,
    cuatrimestre    SMALLINT NOT NULL,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_alumnos_cuatrimestre CHECK (cuatrimestre BETWEEN 1 AND 12)
);

CREATE INDEX idx_alumnos_carrera ON alumnos (carrera_id);

CREATE TRIGGER trg_alumnos_actualizado_en
    BEFORE UPDATE ON alumnos
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();

-- ------------------------------------------------------------
-- Tabla: profesores
-- ------------------------------------------------------------
CREATE TABLE profesores (
    id                  BIGSERIAL PRIMARY KEY,
    usuario_id          BIGINT NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE ON UPDATE CASCADE,
    numero_empleado     VARCHAR(30) NOT NULL UNIQUE,
    especialidad        VARCHAR(150),
    creado_en           TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_profesores_actualizado_en
    BEFORE UPDATE ON profesores
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();

-- ------------------------------------------------------------
-- Tabla: materias
-- ------------------------------------------------------------
CREATE TABLE materias (
    id              BIGSERIAL PRIMARY KEY,
    clave           VARCHAR(30) NOT NULL UNIQUE,
    nombre          VARCHAR(150) NOT NULL,
    descripcion     TEXT,
    activa          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_materias_nombre ON materias (nombre);
CREATE INDEX idx_materias_activa ON materias (activa);

CREATE TRIGGER trg_materias_actualizado_en
    BEFORE UPDATE ON materias
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();

-- ------------------------------------------------------------
-- Tabla: clases
-- ------------------------------------------------------------
CREATE TABLE clases (
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

CREATE INDEX idx_clases_materia ON clases (materia_id);
CREATE INDEX idx_clases_periodo ON clases (periodo_id);
CREATE INDEX idx_clases_activa ON clases (activa);

CREATE TRIGGER trg_clases_actualizado_en
    BEFORE UPDATE ON clases
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();

-- ------------------------------------------------------------
-- Tabla: clase_profesores
-- ------------------------------------------------------------
CREATE TABLE clase_profesores (
    clase_id        BIGINT NOT NULL REFERENCES clases(id) ON DELETE CASCADE ON UPDATE CASCADE,
    profesor_id     BIGINT NOT NULL REFERENCES profesores(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    es_titular      BOOLEAN NOT NULL DEFAULT TRUE,
    asignado_en     TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (clase_id, profesor_id)
);

CREATE INDEX idx_clase_profesores_profesor ON clase_profesores (profesor_id);

-- ------------------------------------------------------------
-- Tabla: inscripciones
-- ------------------------------------------------------------
CREATE TABLE inscripciones (
    id              BIGSERIAL PRIMARY KEY,
    clase_id        BIGINT NOT NULL REFERENCES clases(id) ON DELETE CASCADE ON UPDATE CASCADE,
    alumno_id       BIGINT NOT NULL REFERENCES alumnos(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    estado          estado_inscripcion NOT NULL DEFAULT 'ACTIVO',
    inscrito_en     TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_inscripcion_clase_alumno UNIQUE (clase_id, alumno_id)
);

CREATE INDEX idx_inscripciones_alumno ON inscripciones (alumno_id);
CREATE INDEX idx_inscripciones_estado ON inscripciones (estado);

CREATE TRIGGER trg_inscripciones_actualizado_en
    BEFORE UPDATE ON inscripciones
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();

-- ------------------------------------------------------------
-- Tabla: materiales
-- ------------------------------------------------------------
CREATE TABLE materiales (
    id                          BIGSERIAL PRIMARY KEY,
    clase_id                    BIGINT NOT NULL REFERENCES clases(id) ON DELETE CASCADE ON UPDATE CASCADE,
    profesor_id                 BIGINT NOT NULL REFERENCES profesores(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    titulo                      VARCHAR(200) NOT NULL,
    descripcion_corta           VARCHAR(500),
    introduccion                TEXT NOT NULL,
    objetivo                    TEXT NOT NULL,
    metodologia_trabajo         TEXT NOT NULL,
    detalles_material            TEXT NOT NULL,
    referencias_bibliograficas  TEXT NOT NULL,
    conclusion                  TEXT NOT NULL,
    portada_ruta                VARCHAR(500),
    estado                      estado_material NOT NULL DEFAULT 'BORRADOR',
    alcance                     alcance_material NOT NULL DEFAULT 'TODA_LA_CLASE',
    permite_descarga            BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_publicacion           TIMESTAMP,
    activo                      BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en                   TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en               TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_materiales_clase ON materiales (clase_id);
CREATE INDEX idx_materiales_profesor ON materiales (profesor_id);
CREATE INDEX idx_materiales_estado ON materiales (estado);
CREATE INDEX idx_materiales_publicacion ON materiales (fecha_publicacion);
CREATE INDEX idx_materiales_activo ON materiales (activo);

CREATE TRIGGER trg_materiales_actualizado_en
    BEFORE UPDATE ON materiales
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();

-- ------------------------------------------------------------
-- Tabla: material_alumnos
-- ------------------------------------------------------------
CREATE TABLE material_alumnos (
    material_id     BIGINT NOT NULL REFERENCES materiales(id) ON DELETE CASCADE ON UPDATE CASCADE,
    alumno_id       BIGINT NOT NULL REFERENCES alumnos(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    asignado_en     TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (material_id, alumno_id)
);

CREATE INDEX idx_material_alumnos_alumno ON material_alumnos (alumno_id);

-- ------------------------------------------------------------
-- Tabla: recursos_material
-- ------------------------------------------------------------
CREATE TABLE recursos_material (
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

CREATE INDEX idx_recursos_material ON recursos_material (material_id);
CREATE INDEX idx_recursos_tipo ON recursos_material (tipo);
CREATE INDEX idx_recursos_orden ON recursos_material (material_id, orden);

-- ------------------------------------------------------------
-- Tabla: consultas_material
-- ------------------------------------------------------------
CREATE TABLE consultas_material (
    id                  BIGSERIAL PRIMARY KEY,
    material_id         BIGINT NOT NULL REFERENCES materiales(id) ON DELETE CASCADE ON UPDATE CASCADE,
    alumno_id           BIGINT NOT NULL REFERENCES alumnos(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    primera_consulta    TIMESTAMP NOT NULL DEFAULT NOW(),
    ultima_consulta     TIMESTAMP NOT NULL DEFAULT NOW(),
    numero_consultas    INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT uq_consulta_material_alumno UNIQUE (material_id, alumno_id)
);

CREATE INDEX idx_consultas_alumno ON consultas_material (alumno_id);
CREATE INDEX idx_consultas_ultima ON consultas_material (ultima_consulta);

COMMIT;
