"""
LMS UPQ - Verificación / creación del usuario Administrador inicial
=====================================================================

Este script es IDEMPOTENTE:
  1. Se conecta a la base de datos PostgreSQL.
  2. Verifica si ya existe un usuario con rol ADMINISTRADOR.
  3. Si YA EXISTE  -> no hace nada más (no vuelve a crear ni modificar).
  4. Si NO EXISTE  -> crea el rol ADMINISTRADOR (si hace falta) y crea
     el usuario administrador con la contraseña indicada.

Requiere que 01_schema.sql (y opcionalmente 02_seed_roles.sql) ya se
hayan ejecutado contra la base de datos.

Uso:
    python 03_init_admin.py

Variables de entorno soportadas (todas opcionales, con valores por
defecto pensados para desarrollo local):

    DATABASE_URL            postgresql://usuario:password@host:puerto/bd
    ADMIN_NOMBRE            Nombre del administrador            (default: Admin)
    ADMIN_APELLIDO_PATERNO  Apellido paterno                    (default: UPQ)
    ADMIN_APELLIDO_MATERNO  Apellido materno                    (default: Sistema)
    ADMIN_CORREO            Correo institucional                (default: admin@upq.edu.mx)
    ADMIN_PASSWORD          Contraseña inicial                  (si no se define, se solicita
                                                                  de forma interactiva y oculta)

Dependencias:
    pip install psycopg2-binary python-dotenv werkzeug
"""

import os
import sys
from getpass import getpass

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    sys.exit(
        "Falta la dependencia psycopg2-binary.\n"
        "Instálala con: pip install psycopg2-binary"
    )

try:
    from werkzeug.security import generate_password_hash
except ImportError:
    sys.exit(
        "Falta la dependencia werkzeug (ya viene con Flask).\n"
        "Instálala con: pip install werkzeug"
    )

try:
    from dotenv import load_dotenv
    # override=True: si ya existe una variable DATABASE_URL "vieja" en la
    # sesión de la terminal (por ejemplo, de una prueba anterior con MySQL),
    # el valor del archivo .env tiene prioridad para evitar confusiones.
    load_dotenv(override=True)
except ImportError:
    # python-dotenv es opcional: si no está instalado simplemente
    # se usan las variables de entorno ya presentes en el sistema.
    pass


DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/lms_upq"

ROL_ADMINISTRADOR = "ADMINISTRADOR"
ROL_DESCRIPCION = "Gestiona usuarios, materias, clases y asignaciones"


def normalizar_dsn(url):
    """
    Acepta tanto 'postgresql://...' (libpq) como 'postgresql+psycopg2://...'
    (formato de SQLAlchemy) y valida que sea una URL de PostgreSQL.
    """
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql://", 1)

    if url.startswith("postgres+psycopg2://"):
        return url.replace("postgres+psycopg2://", "postgresql://", 1)

    if not url.startswith("postgresql://") and not url.startswith("postgres://"):
        sys.exit(
            "DATABASE_URL no parece ser una cadena de conexión de "
            f"PostgreSQL válida:\n  {url}\n\n"
            "Debe verse así:\n"
            "  DATABASE_URL=postgresql://usuario:password@host:5432/lms_upq"
        )

    return url


def obtener_conexion():
    """
    En vez de pasarle a psycopg2 el DSN completo como una sola cadena,
    se parsea y se conecta con parámetros individuales. Esto evita un
    bug conocido de psycopg2 en Windows: cuando el DSN de texto trae
    caracteres no-ASCII (tildes, ñ, etc. en usuario/contraseña/host),
    el parser interno de la cadena de conexión lanza
    UnicodeDecodeError al reconstruirla. Pasando los parámetros por
    separado y fijando client_encoding='utf8' se evita el problema.
    """
    from urllib.parse import urlparse, unquote

    raw_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    url = normalizar_dsn(raw_url)

    partes = urlparse(url)

    try:
        return psycopg2.connect(
            host=partes.hostname or "localhost",
            port=partes.port or 5432,
            dbname=(partes.path or "/lms_upq").lstrip("/"),
            user=unquote(partes.username) if partes.username else None,
            password=unquote(partes.password) if partes.password else None,
            client_encoding="utf8",
            # Fuerza a PostgreSQL a devolver los mensajes de error en
            # inglés/ASCII para ESTA conexión. Muchas instalaciones de
            # PostgreSQL en Windows en español configuran lc_messages
            # en español (ej. "la autenticación password falló"), y
            # esos mensajes con tildes/ñ hacen que psycopg2 en Windows
            # lance UnicodeDecodeError en vez de mostrar el error real.
            options="-c lc_messages=C",
        )
    except UnicodeDecodeError:
        sys.exit(
            "PostgreSQL devolvió un mensaje de error en español (con "
            "tildes/ñ) que psycopg2 no pudo decodificar en Windows, por "
            "lo que no se puede ver el error real desde este script.\n\n"
            "Verifica manualmente con psql, que sí muestra el mensaje "
            "correctamente:\n"
            '  psql -U tu_usuario -h localhost -p 5432 -d lms_upq\n\n'
            "Causas más comunes: contraseña incorrecta, la base de datos "
            "'lms_upq' no existe todavía, o el servicio de PostgreSQL no "
            "está corriendo."
        )
    except psycopg2.OperationalError as error:
        sys.exit(f"No fue posible conectar a la base de datos:\n{error}")


def obtener_o_crear_rol_admin(cursor):
    cursor.execute(
        "SELECT id FROM roles WHERE nombre = %s",
        (ROL_ADMINISTRADOR,),
    )
    fila = cursor.fetchone()

    if fila:
        return fila["id"]

    cursor.execute(
        """
        INSERT INTO roles (nombre, descripcion)
        VALUES (%s, %s)
        RETURNING id
        """,
        (ROL_ADMINISTRADOR, ROL_DESCRIPCION),
    )

    return cursor.fetchone()["id"]


def existe_administrador(cursor):
    cursor.execute(
        """
        SELECT u.id, u.correo
        FROM usuarios u
        JOIN roles r ON r.id = u.rol_id
        WHERE r.nombre = %s
        LIMIT 1
        """,
        (ROL_ADMINISTRADOR,),
    )

    return cursor.fetchone()


def solicitar_datos_admin():
    nombre = os.getenv("ADMIN_NOMBRE", "Admin")
    apellido_paterno = os.getenv("ADMIN_APELLIDO_PATERNO", "UPQ")
    apellido_materno = os.getenv("ADMIN_APELLIDO_MATERNO", "Sistema")
    correo = os.getenv("ADMIN_CORREO", "admin@upq.edu.mx").strip().lower()

    password = os.getenv("ADMIN_PASSWORD")

    if not password:
        password = getpass(
            f"Define la contraseña inicial para {correo}: "
        )

        confirmacion = getpass("Confirma la contraseña: ")

        if password != confirmacion:
            sys.exit("Las contraseñas no coinciden. Operación cancelada.")

        if len(password) < 8:
            sys.exit("La contraseña debe tener al menos 8 caracteres.")

    return {
        "nombre": nombre,
        "apellido_paterno": apellido_paterno,
        "apellido_materno": apellido_materno,
        "correo": correo,
        "password": password,
    }


def crear_administrador(cursor, rol_id, datos):
    cursor.execute(
        """
        INSERT INTO usuarios (
            rol_id, nombre, apellido_paterno, apellido_materno,
            correo, password_hash, activo
        )
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        RETURNING id, correo
        """,
        (
            rol_id,
            datos["nombre"],
            datos["apellido_paterno"],
            datos["apellido_materno"],
            datos["correo"],
            generate_password_hash(datos["password"]),
        ),
    )

    return cursor.fetchone()


def main():
    conexion = obtener_conexion()
    conexion.autocommit = False

    try:
        cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        administrador_existente = existe_administrador(cursor)

        if administrador_existente:
            print(
                "Ya existe un usuario administrador en la base de datos "
                f"({administrador_existente['correo']}). "
                "No se realiza ninguna creación."
            )
            conexion.rollback()
            return

        print("No se encontró ningún usuario administrador. Creando uno nuevo...")

        rol_id = obtener_o_crear_rol_admin(cursor)
        datos = solicitar_datos_admin()

        correo_duplicado_query = "SELECT id FROM usuarios WHERE correo = %s"
        cursor.execute(correo_duplicado_query, (datos["correo"],))

        if cursor.fetchone():
            conexion.rollback()
            sys.exit(
                f"Ya existe un usuario (no administrador) con el correo "
                f"{datos['correo']}. Usa otro correo o revisa manualmente."
            )

        nuevo_admin = crear_administrador(cursor, rol_id, datos)

        conexion.commit()

        print(
            "Administrador creado correctamente:\n"
            f"  id:     {nuevo_admin['id']}\n"
            f"  correo: {nuevo_admin['correo']}"
        )

    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    main()