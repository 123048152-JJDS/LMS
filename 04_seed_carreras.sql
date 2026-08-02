-- ============================================================
-- LMS UPQ - Oferta académica (idempotente)
-- Ingenierías y Licenciaturas de la Universidad Politécnica de
-- Querétaro. Sistema cuatrimestral.
-- Ejecutar después de 01_schema.sql:
--   psql "$DATABASE_URL" -f 04_seed_carreras.sql
-- ============================================================

INSERT INTO carreras (clave, nombre, activa) VALUES
    -- Ingenierías
    ('IMECA',  'Ingeniería Mecatrónica', TRUE),
    ('ITAUTO', 'Ingeniería en Tecnología Automotriz', TRUE),
    ('ITIID',  'Ingeniería en Tecnologías de la Información e Innovación Digital', TRUE),
    ('ISC',    'Ingeniería en Sistemas Computacionales', TRUE),
    ('ITMA',   'Ingeniería en Tecnologías de Manufactura / Manufactura Avanzada', TRUE),
    ('IRT',    'Ingeniería en Redes y Telecomunicaciones', TRUE),
    ('IAD',    'Inteligencia Artificial y Datos', TRUE),

    -- Licenciaturas
    ('LAGE',   'Administración y Gestión Empresarial / Administración', TRUE),
    ('LCIA',   'Comercio Internacional y Aduanas / Negocios Internacionales', TRUE)

ON CONFLICT (clave) DO NOTHING;