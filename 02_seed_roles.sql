-- ============================================================
-- LMS UPQ - Catálogo base de roles (idempotente)
-- Ejecutar después de 01_schema.sql:
--   psql -U <usuario> -d lms_upq -f 02_seed_roles.sql
-- ============================================================

INSERT INTO roles (nombre, descripcion) VALUES
    ('ADMINISTRADOR', 'Gestiona usuarios, materias, clases y asignaciones'),
    ('PROFESOR',       'Crea y publica materiales educativos'),
    ('ALUMNO',         'Consulta los materiales educativos asignados')
ON CONFLICT (nombre) DO NOTHING;
