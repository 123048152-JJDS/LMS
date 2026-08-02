# LMS UPQ — Inicialización de base de datos en PostgreSQL

Estos scripts crean **desde cero** la base de datos del LMS en PostgreSQL
(convertida desde `models.py`, que actualmente usa tipos de MySQL) y
verifican que exista el usuario **Administrador**, creándolo solo si
no existe.

## Archivos

| Archivo              | Propósito                                                              |
|-----------------------|-------------------------------------------------------------------------|
| `01_schema.sql`      | Crea tipos ENUM, tablas, índices, llaves foráneas y triggers.           |
| `02_seed_roles.sql`  | Inserta los 3 roles base (ADMINISTRADOR, PROFESOR, ALUMNO) si no existen.|
| `04_seed_carreras.sql` | Inserta la oferta académica real de la UPQ (ingenierías y licenciaturas), si no existen. |
| `03_init_admin.py`   | **Idempotente**: si ya hay un administrador, no hace nada; si no, lo crea.|
| `run_init.sh`        | Ejecuta los pasos anteriores en orden.                                  |

## 1. Crear la base de datos vacía

```bash
createdb -U postgres lms_upq
# o bien:
psql -U postgres -c "CREATE DATABASE lms_upq;"
```

## 2. Ejecutar la inicialización

### Opción A — todo junto

```bash
cd postgresql
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/lms_upq" ./run_init.sh
```

### Opción B — paso a paso

```bash
psql "$DATABASE_URL" -f 01_schema.sql
psql "$DATABASE_URL" -f 02_seed_roles.sql
python3 03_init_admin.py
```

Al ejecutar `03_init_admin.py`:

- **Si ya existe un usuario con rol ADMINISTRADOR** → el script imprime
  un mensaje indicando que ya existe y **no ejecuta ninguna inserción**.
- **Si no existe** → pide (o toma de variables de entorno) nombre,
  apellidos, correo y contraseña, y crea el rol ADMINISTRADOR (si
  hiciera falta) y el usuario.

Puedes automatizar la creación sin prompts definiendo variables de
entorno antes de ejecutar el script:

```bash
export ADMIN_NOMBRE="Admin"
export ADMIN_APELLIDO_PATERNO="UPQ"
export ADMIN_APELLIDO_MATERNO="Sistema"
export ADMIN_CORREO="admin@upq.edu.mx"
export ADMIN_PASSWORD="una-contraseña-segura"
python3 03_init_admin.py
```

## 3. Dependencias de Python

```bash
pip install psycopg2-binary python-dotenv werkzeug
```

(`werkzeug` ya viene incluido si tienes Flask instalado, como en
`requirements.txt` del proyecto.)

## 4. Conectar la aplicación Flask a PostgreSQL

Actualmente `config.py` y `.env` apuntan a MySQL
(`mysql+pymysql://...`). Para usar la nueva base en PostgreSQL:

1. Agrega el driver a `requirements.txt`:

   ```
   psycopg2-binary
   ```

2. Cambia `DATABASE_URL` en `.env`:

   ```
   DATABASE_URL=postgresql+psycopg2://usuario:password@localhost:5432/lms_upq
   ```

3. En `models.py`, reemplaza los tipos específicos de MySQL
   (`sqlalchemy.dialects.mysql.BIGINT/TINYINT/ENUM/LONGTEXT`) por los
   tipos genéricos de SQLAlchemy (`db.BigInteger`, `db.SmallInteger`,
   `db.Enum(...)`, `db.Text`), ya que este esquema PostgreSQL usa tipos
   `ENUM` nativos de Postgres (`estado_inscripcion`, `estado_material`,
   `alcance_material`, `tipo_recurso`) en vez de los `ENUM` de MySQL.

> **Nota:** este cambio de motor (MySQL → PostgreSQL) también resuelve
> la inconsistencia detectada entre el Marco Teórico del reporte
> (que documenta PostgreSQL) y el código actual (que usa MySQL).