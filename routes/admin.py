from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash
from datetime import date

from extensions import db
from models import (
    Alumno,
    Carrera,
    Clase,
    ClaseProfesor,
    Inscripcion,
    Materia,
    PeriodoAcademico,
    Profesor,
    Rol,
    Usuario,
)
from routes.decorators import role_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def get_role(nombre):
    nombre = nombre.strip().upper()

    rol = Rol.query.filter_by(nombre=nombre).first()

    if rol is None:
        rol = Rol(
            nombre=nombre,
            descripcion=f"Rol {nombre}"
        )
        db.session.add(rol)
        db.session.flush()

    return rol


def form_bool(nombre):
    return request.form.get(nombre) in {"on", "true", "1", "si", "sí"}


def obtener_apellidos_desde_formulario():
    apellido_paterno = request.form.get("apellido_paterno", "").strip()
    apellido_materno = request.form.get("apellido_materno", "").strip()

    if apellido_paterno:
        return apellido_paterno, apellido_materno

    apellidos = request.form.get("apellidos", "").strip().split()

    if not apellidos:
        return "", ""

    apellido_paterno = apellidos[0]
    apellido_materno = " ".join(apellidos[1:]) if len(apellidos) > 1 else ""

    return apellido_paterno, apellido_materno


@admin_bp.route("/dashboard")
@role_required("ADMINISTRADOR")
def dashboard():
    hoy = date.today()
    inicio_mes = date(hoy.year, hoy.month, 1)

    stats = {
        "alumnos": Alumno.query.join(Usuario).filter(Usuario.activo.is_(True)).count(),
        "profesores": Profesor.query.join(Usuario).filter(Usuario.activo.is_(True)).count(),
        "materias": Materia.query.filter(Materia.activa.is_(True)).count(),
        "clases": Clase.query.filter(Clase.activa.is_(True)).count(),

        "clases_mes": Clase.query.filter(Clase.creado_en >= inicio_mes).count(),
        "usuarios_mes": Usuario.query.filter(Usuario.creado_en >= inicio_mes).count(),
        "clases_activas": Clase.query.filter(Clase.activa.is_(True)).count(),
        "clases_inactivas": Clase.query.filter(Clase.activa.is_(False)).count(),
    }

    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/usuarios/<tipo>")
@role_required("ADMINISTRADOR")
def usuarios(tipo):
    if tipo not in {"alumnos", "profesores"}:
        return render_template("errors/404.html"), 404

    rol_nombre = "ALUMNO" if tipo == "alumnos" else "PROFESOR"

    usuarios_lista = (
        Usuario.query
        .join(Rol)
        .filter(Rol.nombre == rol_nombre)
        .order_by(
            Usuario.apellido_paterno,
            Usuario.apellido_materno,
            Usuario.nombre
        )
        .all()
    )

    return render_template(
        "admin/usuarios.html",
        usuarios=usuarios_lista,
        tipo=tipo
    )


@admin_bp.route("/usuarios/<tipo>/nuevo", methods=["GET", "POST"])
@role_required("ADMINISTRADOR")
def crear_usuario(tipo):
    if tipo not in {"alumnos", "profesores"}:
        return render_template("errors/404.html"), 404

    usuario = Usuario(activo=True)
    perfil = Alumno() if tipo == "alumnos" else Profesor()

    return guardar_usuario(
        tipo=tipo,
        usuario=usuario,
        perfil=perfil,
        nuevo=True
    )


@admin_bp.route("/usuarios/<tipo>/<int:usuario_id>/editar", methods=["GET", "POST"])
@role_required("ADMINISTRADOR")
def editar_usuario(tipo, usuario_id):
    if tipo not in {"alumnos", "profesores"}:
        return render_template("errors/404.html"), 404

    usuario = Usuario.query.get_or_404(usuario_id)

    perfil = usuario.alumno if tipo == "alumnos" else usuario.profesor

    if perfil is None:
        return render_template("errors/404.html"), 404

    return guardar_usuario(
        tipo=tipo,
        usuario=usuario,
        perfil=perfil,
        nuevo=False
    )


def guardar_usuario(tipo, usuario, perfil, nuevo):
    carreras = (
        Carrera.query
        .filter(Carrera.activa.is_(True))
        .order_by(Carrera.nombre)
        .all()
    )

    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        identificador = request.form.get("identificador", "").strip()
        nombre = request.form.get("nombre", "").strip()
        password = request.form.get("password", "").strip()

        apellido_paterno, apellido_materno = obtener_apellidos_desde_formulario()

        if not correo or not identificador or not nombre or not apellido_paterno:
            flash("Completa los campos obligatorios.", "danger")
            return render_template(
                "admin/formulario_usuario.html",
                usuario=usuario,
                perfil=perfil,
                tipo=tipo,
                carreras=carreras
            )

        correo_duplicado = (
            Usuario.query
            .filter(
                Usuario.correo == correo,
                Usuario.id != (usuario.id or 0)
            )
            .first()
        )

        if correo_duplicado:
            flash("El correo ya está registrado.", "danger")
            return render_template(
                "admin/formulario_usuario.html",
                usuario=usuario,
                perfil=perfil,
                tipo=tipo,
                carreras=carreras
            )

        if tipo == "alumnos":
            matricula_duplicada = (
                Alumno.query
                .filter(
                    Alumno.matricula == identificador,
                    Alumno.id != (perfil.id or 0)
                )
                .first()
            )

            if matricula_duplicada:
                flash("La matrícula ya está registrada.", "danger")
                return render_template(
                    "admin/formulario_usuario.html",
                    usuario=usuario,
                    perfil=perfil,
                    tipo=tipo,
                    carreras=carreras
                )

            carrera_id = request.form.get("carrera_id")
            cuatrimestre = request.form.get("cuatrimestre")

            if not carrera_id or not cuatrimestre:
                flash("Selecciona la carrera y el cuatrimestre.", "danger")
                return render_template(
                    "admin/formulario_usuario.html",
                    usuario=usuario,
                    perfil=perfil,
                    tipo=tipo,
                    carreras=carreras
                )

        if tipo == "profesores":
            empleado_duplicado = (
                Profesor.query
                .filter(
                    Profesor.numero_empleado == identificador,
                    Profesor.id != (perfil.id or 0)
                )
                .first()
            )

            if empleado_duplicado:
                flash("El número de empleado ya está registrado.", "danger")
                return render_template(
                    "admin/formulario_usuario.html",
                    usuario=usuario,
                    perfil=perfil,
                    tipo=tipo,
                    carreras=carreras
                )

        usuario.nombre = nombre
        usuario.apellido_paterno = apellido_paterno
        usuario.apellido_materno = apellido_materno or None
        usuario.correo = correo
        usuario.activo = form_bool("activo")
        usuario.rol = get_role("ALUMNO" if tipo == "alumnos" else "PROFESOR")

        if password:
            usuario.password_hash = generate_password_hash(password)
        elif nuevo:
            usuario.password_hash = generate_password_hash(identificador)

        db.session.add(usuario)
        db.session.flush()

        perfil.usuario_id = usuario.id

        if tipo == "alumnos":
            perfil.matricula = identificador
            perfil.carrera_id = int(request.form.get("carrera_id"))
            perfil.cuatrimestre = int(request.form.get("cuatrimestre"))

        if tipo == "profesores":
            perfil.numero_empleado = identificador
            perfil.especialidad = request.form.get("especialidad", "").strip() or None

        db.session.add(perfil)
        db.session.commit()

        flash("Usuario guardado correctamente.", "success")
        return redirect(url_for("admin.usuarios", tipo=tipo))

    return render_template(
        "admin/formulario_usuario.html",
        usuario=usuario,
        perfil=perfil,
        tipo=tipo,
        carreras=carreras
    )


@admin_bp.route("/usuarios/<tipo>/<int:usuario_id>/desactivar", methods=["POST"])
@role_required("ADMINISTRADOR")
def desactivar_usuario(tipo, usuario_id):
    if tipo not in {"alumnos", "profesores"}:
        return render_template("errors/404.html"), 404

    usuario = Usuario.query.get_or_404(usuario_id)
    usuario.activo = False

    db.session.commit()

    flash("Usuario desactivado correctamente.", "success")
    return redirect(url_for("admin.usuarios", tipo=tipo))


@admin_bp.route("/carreras")
@role_required("ADMINISTRADOR")
def carreras():
    carreras_lista = Carrera.query.order_by(Carrera.nombre).all()

    return render_template(
        "admin/carreras.html",
        carreras=carreras_lista
    )


@admin_bp.route("/carreras/nueva", methods=["GET", "POST"])
@admin_bp.route("/carreras/<int:carrera_id>/editar", methods=["GET", "POST"])
@role_required("ADMINISTRADOR")
def formulario_carrera(carrera_id=None):
    carrera = (
        Carrera.query.get_or_404(carrera_id)
        if carrera_id
        else Carrera(activa=True)
    )

    if request.method == "POST":
        clave = request.form.get("clave", "").strip().upper()
        nombre = request.form.get("nombre", "").strip()

        if not clave or not nombre:
            flash("La clave y el nombre de la carrera son obligatorios.", "danger")
            return render_template(
                "admin/formulario_carrera.html",
                carrera=carrera
            )

        clave_duplicada = (
            Carrera.query
            .filter(
                Carrera.clave == clave,
                Carrera.id != (carrera.id or 0)
            )
            .first()
        )

        if clave_duplicada:
            flash("La clave de carrera ya existe.", "danger")
            return render_template(
                "admin/formulario_carrera.html",
                carrera=carrera
            )

        carrera.clave = clave
        carrera.nombre = nombre
        carrera.activa = form_bool("activa") or form_bool("activo")

        db.session.add(carrera)
        db.session.commit()

        flash("Carrera guardada correctamente.", "success")
        return redirect(url_for("admin.carreras"))

    return render_template(
        "admin/formulario_carrera.html",
        carrera=carrera
    )


@admin_bp.route("/materias")
@role_required("ADMINISTRADOR")
def materias():
    materias_lista = Materia.query.order_by(Materia.nombre).all()

    return render_template(
        "admin/materias.html",
        materias=materias_lista
    )


@admin_bp.route("/materias/nueva", methods=["GET", "POST"])
@admin_bp.route("/materias/<int:materia_id>/editar", methods=["GET", "POST"])
@role_required("ADMINISTRADOR")
def formulario_materia(materia_id=None):
    materia = (
        Materia.query.get_or_404(materia_id)
        if materia_id
        else Materia(activa=True)
    )

    if request.method == "POST":
        clave = request.form.get("clave", "").strip().upper()
        nombre = request.form.get("nombre", "").strip()

        if not clave or not nombre:
            flash("La clave y el nombre de la materia son obligatorios.", "danger")
            return render_template(
                "admin/formulario_materia.html",
                materia=materia
            )

        clave_duplicada = (
            Materia.query
            .filter(
                Materia.clave == clave,
                Materia.id != (materia.id or 0)
            )
            .first()
        )

        if clave_duplicada:
            flash("La clave de materia ya existe.", "danger")
            return render_template(
                "admin/formulario_materia.html",
                materia=materia
            )

        materia.clave = clave
        materia.nombre = nombre
        materia.descripcion = request.form.get("descripcion", "").strip() or None
        materia.activa = form_bool("activa") or form_bool("activo")

        db.session.add(materia)
        db.session.commit()

        flash("Materia guardada correctamente.", "success")
        return redirect(url_for("admin.materias"))

    return render_template(
        "admin/formulario_materia.html",
        materia=materia
    )


@admin_bp.route("/periodos")
@role_required("ADMINISTRADOR")
def periodos():
    periodos_lista = (
        PeriodoAcademico.query
        .order_by(PeriodoAcademico.fecha_inicio.desc())
        .all()
    )

    return render_template(
        "admin/periodos.html",
        periodos=periodos_lista
    )


@admin_bp.route("/periodos/nuevo", methods=["GET", "POST"])
@admin_bp.route("/periodos/<int:periodo_id>/editar", methods=["GET", "POST"])
@role_required("ADMINISTRADOR")
def formulario_periodo(periodo_id=None):
    periodo = (
        PeriodoAcademico.query.get_or_404(periodo_id)
        if periodo_id
        else PeriodoAcademico(activo=True)
    )

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        fecha_inicio_raw = request.form.get("fecha_inicio", "").strip()
        fecha_fin_raw = request.form.get("fecha_fin", "").strip()

        if not nombre or not fecha_inicio_raw or not fecha_fin_raw:
            flash("Completa el nombre y ambas fechas del periodo.", "danger")
            return render_template("admin/formulario_periodo.html", periodo=periodo)

        try:
            fecha_inicio = date.fromisoformat(fecha_inicio_raw)
            fecha_fin = date.fromisoformat(fecha_fin_raw)
        except ValueError:
            flash("Las fechas capturadas no son válidas.", "danger")
            return render_template("admin/formulario_periodo.html", periodo=periodo)

        if fecha_fin < fecha_inicio:
            flash("La fecha de fin no puede ser anterior a la fecha de inicio.", "danger")
            return render_template("admin/formulario_periodo.html", periodo=periodo)

        nombre_duplicado = (
            PeriodoAcademico.query
            .filter(
                PeriodoAcademico.nombre == nombre,
                PeriodoAcademico.id != (periodo.id or 0)
            )
            .first()
        )

        if nombre_duplicado:
            flash("Ya existe un periodo académico con ese nombre.", "danger")
            return render_template("admin/formulario_periodo.html", periodo=periodo)

        periodo.nombre = nombre
        periodo.fecha_inicio = fecha_inicio
        periodo.fecha_fin = fecha_fin
        periodo.activo = form_bool("activo")

        db.session.add(periodo)
        db.session.commit()

        flash("Periodo académico guardado correctamente.", "success")
        return redirect(url_for("admin.periodos"))

    return render_template(
        "admin/formulario_periodo.html",
        periodo=periodo
    )


@admin_bp.route("/clases")
@role_required("ADMINISTRADOR")
def clases():
    clases_lista = (
        Clase.query
        .order_by(Clase.id.desc())
        .all()
    )

    return render_template(
        "admin/clases.html",
        clases=clases_lista
    )


@admin_bp.route("/clases/nueva", methods=["GET", "POST"])
@admin_bp.route("/clases/<int:clase_id>/editar", methods=["GET", "POST"])
@role_required("ADMINISTRADOR")
def formulario_clase(clase_id=None):
    clase = (
        Clase.query.get_or_404(clase_id)
        if clase_id
        else Clase(activa=True)
    )

    materias = (
        Materia.query
        .filter(Materia.activa.is_(True))
        .order_by(Materia.nombre)
        .all()
    )

    periodos = (
        PeriodoAcademico.query
        .order_by(PeriodoAcademico.nombre)
        .all()
    )

    if request.method == "POST":
        materia_id = request.form.get("materia_id")
        periodo_id = request.form.get("periodo_id")

        nombre_grupo = (
            request.form.get("nombre_grupo")
            or request.form.get("grupo")
            or ""
        ).strip().upper()

        codigo_clase = (
            request.form.get("codigo_clase")
            or request.form.get("codigo")
            or ""
        ).strip().upper()

        if not materia_id or not periodo_id or not nombre_grupo:
            flash("Selecciona materia, periodo y nombre del grupo.", "danger")
            return render_template(
                "admin/formulario_clase.html",
                clase=clase,
                materias=materias,
                periodos=periodos
            )

        if not codigo_clase:
            codigo_clase = f"M{materia_id}-P{periodo_id}-{nombre_grupo}"

        codigo_duplicado = (
            Clase.query
            .filter(
                Clase.codigo_clase == codigo_clase,
                Clase.id != (clase.id or 0)
            )
            .first()
        )

        if codigo_duplicado:
            flash("El código de clase ya existe.", "danger")
            return render_template(
                "admin/formulario_clase.html",
                clase=clase,
                materias=materias,
                periodos=periodos
            )

        clase.materia_id = int(materia_id)
        clase.periodo_id = int(periodo_id)
        clase.codigo_clase = codigo_clase
        clase.nombre_grupo = nombre_grupo
        clase.descripcion = request.form.get("descripcion", "").strip() or None
        clase.activa = form_bool("activa") or form_bool("activo")

        db.session.add(clase)
        db.session.commit()

        flash("Clase guardada correctamente.", "success")
        return redirect(url_for("admin.clases"))

    return render_template(
        "admin/formulario_clase.html",
        clase=clase,
        materias=materias,
        periodos=periodos
    )


@admin_bp.route("/clases/<int:clase_id>/profesores", methods=["GET", "POST"])
@role_required("ADMINISTRADOR")
def asignar_profesor(clase_id):
    clase = Clase.query.get_or_404(clase_id)

    profesores = (
        Profesor.query
        .join(Usuario)
        .filter(Usuario.activo.is_(True))
        .order_by(
            Usuario.apellido_paterno,
            Usuario.apellido_materno,
            Usuario.nombre
        )
        .all()
    )

    profesores_asignados = {
        asignacion.profesor_id
        for asignacion in clase.profesores
    }

    if request.method == "POST":
        ids = {
            int(item)
            for item in request.form.getlist("profesores")
        }

        ClaseProfesor.query.filter_by(
            clase_id=clase.id
        ).delete(synchronize_session=False)

        for profesor_id in ids:
            db.session.add(
                ClaseProfesor(
                    clase_id=clase.id,
                    profesor_id=profesor_id,
                    es_titular=True
                )
            )

        db.session.commit()

        flash("Profesores asignados correctamente.", "success")
        return redirect(url_for("admin.clases"))

    return render_template(
        "admin/asignar_profesor.html",
        clase=clase,
        profesores=profesores,
        profesores_asignados=profesores_asignados
    )


@admin_bp.route("/clases/<int:clase_id>/alumnos", methods=["GET", "POST"])
@role_required("ADMINISTRADOR")
def asignar_alumnos(clase_id):
    clase = Clase.query.get_or_404(clase_id)

    alumnos = (
        Alumno.query
        .join(Usuario)
        .filter(Usuario.activo.is_(True))
        .order_by(
            Usuario.apellido_paterno,
            Usuario.apellido_materno,
            Usuario.nombre
        )
        .all()
    )

    alumnos_asignados = {
        inscripcion.alumno_id
        for inscripcion in clase.inscripciones
        if inscripcion.estado == "ACTIVO"
    }

    if request.method == "POST":
        seleccionados = {
            int(item)
            for item in request.form.getlist("alumnos")
        }

        for alumno in alumnos:
            inscripcion = Inscripcion.query.filter_by(
                clase_id=clase.id,
                alumno_id=alumno.id
            ).first()

            if alumno.id in seleccionados:
                if inscripcion:
                    inscripcion.estado = "ACTIVO"
                else:
                    db.session.add(
                        Inscripcion(
                            clase_id=clase.id,
                            alumno_id=alumno.id,
                            estado="ACTIVO"
                        )
                    )
            elif inscripcion:
                inscripcion.estado = "BAJA"

        db.session.commit()

        flash("Inscripciones actualizadas correctamente.", "success")
        return redirect(url_for("admin.clases"))

    return render_template(
        "admin/asignar_alumnos.html",
        clase=clase,
        alumnos=alumnos,
        alumnos_asignados=alumnos_asignados
    )