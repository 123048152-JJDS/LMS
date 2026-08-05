"""
LMS UPQ - Material educativo de prueba: Estructura de Datos
================================================================

A diferencia de 05_seed_datos_prueba_isc.py (que crea profesores y
alumnos desde cero), este script asume que YA EXISTEN profesores y
alumnos de prueba en la base de datos (como ya es tu caso) y solo
agrega lo que falta para tener un material educativo real de
ejemplo:

  1. Verifica/crea la materia "Estructura de Datos" (4to cuatrimestre
     de la retícula oficial de ISC que compartiste).
  2. Verifica/crea un periodo académico vigente.
  3. Verifica/crea una Clase para esa materia.
  4. Asigna al primer profesor de prueba encontrado como titular.
  5. Inscribe a los alumnos de prueba encontrados (si no lo estaban).
  6. Crea una Unidad ("Unidad 1: Introducción a las Estructuras de
     Datos").
  7. Crea un Material completo (con las 6 secciones de la metodología
     Uskov redactadas, no placeholders) dentro de esa unidad,
     publicado y con descarga permitida.

Es IDEMPOTENTE: se puede correr varias veces sin duplicar nada.

Uso:
    python 06_seed_material_demo.py
"""

import os
import sys
from urllib.parse import unquote, urlparse

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    sys.exit("Falta psycopg2-binary. Instálalo con: pip install psycopg2-binary")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/lms_upq"

MATERIA_CLAVE = "ISC-27"
MATERIA_NOMBRE = "Estructura de Datos"

PERIODO_NOMBRE = os.getenv("SEED_PERIODO_NOMBRE", "Septiembre-Diciembre 2026")
PERIODO_INICIO = os.getenv("SEED_PERIODO_INICIO", "2026-09-01")
PERIODO_FIN = os.getenv("SEED_PERIODO_FIN", "2026-12-19")

CODIGO_CLASE = "ISC-27-DEMO-A"
NOMBRE_GRUPO = "A"

UNIDAD_TITULO = "Unidad 1: Introducción a las Estructuras de Datos"
UNIDAD_DESCRIPCION = (
    "Fundamentos sobre organización y manipulación eficiente de "
    "datos en memoria: arreglos, listas ligadas, pilas y colas."
)

MATERIAL = {
    "titulo": "Introducción a las Estructuras de Datos Lineales",
    "descripcion_corta": (
        "Panorama general de arreglos, listas ligadas, pilas y colas: "
        "qué problema resuelven, cómo se comparan entre sí y cuándo "
        "conviene usar cada una."
    ),
    "introduccion": (
        "Toda aplicación de software necesita almacenar y organizar "
        "información para poder procesarla de forma eficiente. Una "
        "estructura de datos es precisamente eso: una forma "
        "organizada de guardar un conjunto de datos en memoria, "
        "junto con las operaciones que permiten acceder a ellos, "
        "modificarlos o recorrerlos. La elección de la estructura "
        "correcta afecta directamente el rendimiento de un programa: "
        "la misma tarea puede tomar milisegundos o minutos "
        "dependiendo de si los datos están organizados de la forma "
        "adecuada para el problema que se quiere resolver. En esta "
        "unidad se estudian las estructuras de datos lineales más "
        "utilizadas en la práctica profesional: arreglos, listas "
        "ligadas, pilas y colas."
    ),
    "objetivo": (
        "Al finalizar esta unidad, el alumno será capaz de: "
        "(1) explicar las diferencias de implementación y desempeño "
        "entre arreglos y listas ligadas; "
        "(2) implementar operaciones básicas (inserción, eliminación "
        "y búsqueda) sobre listas ligadas simples; "
        "(3) implementar una pila y una cola usando ambas "
        "representaciones (arreglo y lista ligada); y "
        "(4) seleccionar la estructura de datos más adecuada según "
        "los requisitos de tiempo y espacio de un problema dado."
    ),
    "metodologia_trabajo": (
        "El trabajo de la unidad combina exposición teórica breve "
        "con práctica de codificación inmediata. Cada estructura se "
        "presenta primero de forma conceptual (con diagramas de "
        "memoria), después se analiza su complejidad algorítmica "
        "(notación Big-O) para las operaciones principales, y "
        "finalmente se implementa en el lenguaje de programación "
        "visto en el curso. Se recomienda resolver primero los "
        "ejercicios de trazado en papel (dibujar cómo cambia la "
        "estructura en memoria paso a paso) antes de escribir "
        "código, ya que esto reduce errores de implementación. Al "
        "cierre de la unidad se entrega una práctica integradora que "
        "combina las cuatro estructuras vistas."
    ),
    "detalles_material": (
        "1. Arreglos (arrays): bloque contiguo de memoria de tamaño "
        "fijo. Acceso a cualquier elemento en tiempo constante O(1) "
        "mediante índice, pero insertar o eliminar en medio del "
        "arreglo requiere desplazar elementos, con costo O(n).\n\n"
        "2. Listas ligadas (linked lists): secuencia de nodos donde "
        "cada nodo almacena un dato y una referencia (puntero) al "
        "siguiente nodo. Insertar o eliminar al inicio cuesta O(1), "
        "pero acceder a un elemento por posición requiere recorrer "
        "la lista, con costo O(n). No requieren que la memoria sea "
        "contigua ni de tamaño fijo.\n\n"
        "3. Pilas (stacks): estructura con disciplina LIFO (Last In, "
        "First Out) — el último elemento en entrar es el primero en "
        "salir. Operaciones principales: push (insertar) y pop "
        "(extraer), ambas en O(1). Se usan, por ejemplo, para el "
        "manejo de llamadas a funciones (call stack) y para "
        "deshacer/rehacer acciones.\n\n"
        "4. Colas (queues): estructura con disciplina FIFO (First "
        "In, First Out) — el primer elemento en entrar es el primero "
        "en salir. Operaciones principales: enqueue (insertar al "
        "final) y dequeue (extraer del frente), ambas en O(1) cuando "
        "se implementan correctamente. Se usan en sistemas de "
        "colas de impresión, procesamiento de tareas y algoritmos de "
        "recorrido de grafos como BFS.\n\n"
        "Comparación de complejidad (peor caso):\n"
        "- Acceso por índice: arreglo O(1), lista ligada O(n)\n"
        "- Inserción al inicio: arreglo O(n), lista ligada O(1)\n"
        "- Búsqueda de un valor: ambas O(n)"
    ),
    "referencias_bibliograficas": (
        "Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. "
        "(2022). Introduction to Algorithms (4th ed.). MIT Press.\n\n"
        "Goodrich, M. T., Tamassia, R., & Goldwasser, M. H. (2014). "
        "Data Structures and Algorithms in Python. Wiley.\n\n"
        "Weiss, M. A. (2013). Data Structures and Algorithm Analysis "
        "in C++ (4th ed.). Pearson."
    ),
    "conclusion": (
        "Las estructuras de datos lineales son la base sobre la que "
        "se construyen estructuras más complejas (árboles, tablas "
        "hash, grafos) que se verán en unidades posteriores. No "
        "existe una estructura universalmente mejor: la decisión "
        "correcta siempre depende de qué operación se realiza con "
        "más frecuencia en el problema específico que se está "
        "resolviendo. Dominar el análisis de complejidad permite "
        "justificar esa decisión con criterios técnicos, en vez de "
        "elegir por costumbre."
    ),
}


def normalizar_dsn(url):
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql://", 1)
    if url.startswith("postgres+psycopg2://"):
        return url.replace("postgres+psycopg2://", "postgresql://", 1)
    if not url.startswith("postgresql://") and not url.startswith("postgres://"):
        sys.exit(f"DATABASE_URL inválida: {url}")
    return url


def obtener_conexion():
    url = normalizar_dsn(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
    partes = urlparse(url)

    try:
        return psycopg2.connect(
            host=partes.hostname or "localhost",
            port=partes.port or 5432,
            dbname=(partes.path or "/lms_upq").lstrip("/"),
            user=unquote(partes.username) if partes.username else None,
            password=unquote(partes.password) if partes.password else None,
            client_encoding="utf8",
            options="-c lc_messages=C",
        )
    except psycopg2.OperationalError as error:
        sys.exit(f"No fue posible conectar a la base de datos:\n{error}")


def obtener_o_crear_materia(cur):
    cur.execute("SELECT id FROM materias WHERE nombre = %s", (MATERIA_NOMBRE,))
    fila = cur.fetchone()

    if fila:
        return fila["id"]

    cur.execute(
        """
        INSERT INTO materias (clave, nombre, activa)
        VALUES (%s, %s, TRUE)
        ON CONFLICT (clave) DO UPDATE SET nombre = EXCLUDED.nombre
        RETURNING id
        """,
        (MATERIA_CLAVE, MATERIA_NOMBRE),
    )
    materia_id = cur.fetchone()["id"]
    print(f"Materia creada: {MATERIA_NOMBRE}")
    return materia_id


def obtener_o_crear_periodo(cur):
    cur.execute("SELECT id FROM periodos_academicos WHERE nombre = %s", (PERIODO_NOMBRE,))
    fila = cur.fetchone()

    if fila:
        return fila["id"]

    cur.execute("SELECT id FROM periodos_academicos WHERE activo = TRUE LIMIT 1")
    fila = cur.fetchone()

    if fila:
        return fila["id"]

    cur.execute(
        """
        INSERT INTO periodos_academicos (nombre, fecha_inicio, fecha_fin, activo)
        VALUES (%s, %s, %s, TRUE)
        RETURNING id
        """,
        (PERIODO_NOMBRE, PERIODO_INICIO, PERIODO_FIN),
    )
    periodo_id = cur.fetchone()["id"]
    print(f"Periodo académico creado: {PERIODO_NOMBRE}")
    return periodo_id


def obtener_primer_profesor(cur):
    cur.execute(
        """
        SELECT p.id, u.nombre, u.apellido_paterno, u.correo
        FROM profesores p
        JOIN usuarios u ON u.id = p.usuario_id
        WHERE u.activo = TRUE
        ORDER BY p.id
        LIMIT 1
        """
    )
    fila = cur.fetchone()

    if not fila:
        sys.exit(
            "No hay ningún profesor registrado en la base de datos.\n"
            "Crea al menos uno (por ejemplo con 05_seed_datos_prueba_isc.py "
            "o desde el panel de administrador) antes de correr este script."
        )

    return fila


def obtener_alumnos(cur, limite=10):
    cur.execute(
        """
        SELECT a.id
        FROM alumnos a
        JOIN usuarios u ON u.id = a.usuario_id
        WHERE u.activo = TRUE
        ORDER BY a.id
        LIMIT %s
        """,
        (limite,),
    )
    return [fila["id"] for fila in cur.fetchall()]


def obtener_o_crear_clase(cur, materia_id, periodo_id):
    cur.execute("SELECT id FROM clases WHERE codigo_clase = %s", (CODIGO_CLASE,))
    fila = cur.fetchone()

    if fila:
        return fila["id"]

    cur.execute(
        """
        INSERT INTO clases (materia_id, periodo_id, codigo_clase, nombre_grupo, activa)
        VALUES (%s, %s, %s, %s, TRUE)
        RETURNING id
        """,
        (materia_id, periodo_id, CODIGO_CLASE, NOMBRE_GRUPO),
    )
    clase_id = cur.fetchone()["id"]
    print(f"Clase creada: {CODIGO_CLASE}")
    return clase_id


def asignar_profesor_a_clase(cur, clase_id, profesor_id):
    cur.execute(
        "SELECT 1 FROM clase_profesores WHERE clase_id = %s AND profesor_id = %s",
        (clase_id, profesor_id),
    )

    if cur.fetchone():
        return

    cur.execute(
        """
        INSERT INTO clase_profesores (clase_id, profesor_id, es_titular)
        VALUES (%s, %s, TRUE)
        """,
        (clase_id, profesor_id),
    )
    print("Profesor asignado como titular de la clase.")


def inscribir_alumnos(cur, clase_id, alumnos_ids):
    inscritos = 0

    for alumno_id in alumnos_ids:
        cur.execute(
            "SELECT 1 FROM inscripciones WHERE clase_id = %s AND alumno_id = %s",
            (clase_id, alumno_id),
        )

        if cur.fetchone():
            continue

        cur.execute(
            """
            INSERT INTO inscripciones (clase_id, alumno_id, estado)
            VALUES (%s, %s, 'ACTIVO')
            """,
            (clase_id, alumno_id),
        )
        inscritos += 1

    if inscritos:
        print(f"Alumnos inscritos en la clase de prueba: {inscritos}")


def obtener_o_crear_unidad(cur, clase_id):
    cur.execute(
        "SELECT id FROM unidades WHERE clase_id = %s AND titulo = %s",
        (clase_id, UNIDAD_TITULO),
    )
    fila = cur.fetchone()

    if fila:
        return fila["id"]

    cur.execute(
        """
        INSERT INTO unidades (clase_id, titulo, descripcion, orden, activa)
        VALUES (%s, %s, %s, 1, TRUE)
        RETURNING id
        """,
        (clase_id, UNIDAD_TITULO, UNIDAD_DESCRIPCION),
    )
    unidad_id = cur.fetchone()["id"]
    print(f"Unidad creada: {UNIDAD_TITULO}")
    return unidad_id


def crear_material_si_hace_falta(cur, unidad_id, profesor_id):
    cur.execute(
        "SELECT id FROM materiales WHERE unidad_id = %s AND titulo = %s",
        (unidad_id, MATERIAL["titulo"]),
    )

    if cur.fetchone():
        print("El material de prueba ya existía. No se creó de nuevo.")
        return

    cur.execute(
        """
        INSERT INTO materiales (
            unidad_id, profesor_id, titulo, descripcion_corta,
            introduccion, objetivo, metodologia_trabajo,
            detalles_material, referencias_bibliograficas, conclusion,
            estado, alcance, permite_descarga, fecha_publicacion, activo
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            'PUBLICADO', 'TODA_LA_CLASE', TRUE, NOW(), TRUE
        )
        RETURNING id
        """,
        (
            unidad_id,
            profesor_id,
            MATERIAL["titulo"],
            MATERIAL["descripcion_corta"],
            MATERIAL["introduccion"],
            MATERIAL["objetivo"],
            MATERIAL["metodologia_trabajo"],
            MATERIAL["detalles_material"],
            MATERIAL["referencias_bibliograficas"],
            MATERIAL["conclusion"],
        ),
    )
    material_id = cur.fetchone()["id"]
    print(f"Material creado y publicado: {MATERIAL['titulo']} (id={material_id})")


def main():
    conexion = obtener_conexion()
    conexion.autocommit = False

    try:
        cur = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        materia_id = obtener_o_crear_materia(cur)
        periodo_id = obtener_o_crear_periodo(cur)
        clase_id = obtener_o_crear_clase(cur, materia_id, periodo_id)

        profesor = obtener_primer_profesor(cur)
        asignar_profesor_a_clase(cur, clase_id, profesor["id"])

        alumnos_ids = obtener_alumnos(cur)
        inscribir_alumnos(cur, clase_id, alumnos_ids)

        unidad_id = obtener_o_crear_unidad(cur, clase_id)
        crear_material_si_hace_falta(cur, unidad_id, profesor["id"])

        conexion.commit()

        print("\nListo. Resumen:")
        print(f"  Materia: {MATERIA_NOMBRE}")
        print(f"  Clase:   {CODIGO_CLASE}")
        print(f"  Unidad:  {UNIDAD_TITULO}")
        print(f"  Profesor dueño: {profesor['nombre']} {profesor['apellido_paterno']} ({profesor['correo']})")
        print(f"  Alumnos con acceso: {len(alumnos_ids)}")
        print("\nInicia sesión con ese profesor para verlo en 'Mis materiales',")
        print("o con cualquiera de esos alumnos para verlo en 'Mis clases'.")

    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    main()