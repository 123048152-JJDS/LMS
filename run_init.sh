#!/usr/bin/env bash
# ============================================================
# LMS UPQ - Inicialización completa de la base de datos PostgreSQL
# ============================================================
# Uso:
#   DATABASE_URL="postgresql://usuario:password@host:5432/lms_upq" ./run_init.sh
#
# Requiere: psql (cliente de PostgreSQL) y python3 con
# psycopg2-binary y werkzeug instalados.

set -euo pipefail

DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/lms_upq}"

echo "==> Usando DATABASE_URL: ${DATABASE_URL}"

echo "==> 1/4 Creando esquema (tablas, tipos, índices, triggers)..."
psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f 01_schema.sql

echo "==> 2/4 Sembrando catálogo de roles..."
psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f 02_seed_roles.sql

echo "==> 3/4 Sembrando oferta académica (carreras UPQ)..."
psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f 04_seed_carreras.sql

echo "==> 4/4 Verificando / creando usuario administrador..."
DATABASE_URL="${DATABASE_URL}" python3 03_init_admin.py

echo "==> Inicialización completada."