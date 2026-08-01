from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.dialects.mysql import (
    BIGINT,
    INTEGER,
    TINYINT,
    ENUM,
    LONGTEXT
)

from extensions import db


class Rol(db.Model):
    __tablename__ = "roles"

    id = db.Column(
        TINYINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    nombre = db.Column(
        db.String(30),
        nullable=False,
        unique=True
    )

    descripcion = db.Column(
        db.String(150),
        nullable=True
    )

    creado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    usuarios = db.relationship(
        "Usuario",
        back_populates="rol",
        lazy=True
    )

    def __repr__(self):
        return f"<Rol {self.nombre}>"


class Carrera(db.Model):
    __tablename__ = "carreras"

    id = db.Column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    clave = db.Column(
        db.String(20),
        nullable=False,
        unique=True
    )

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    activa = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    creado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    alumnos = db.relationship(
        "Alumno",
        back_populates="carrera",
        lazy=True
    )

    def __repr__(self):
        return f"<Carrera {self.nombre}>"


class PeriodoAcademico(db.Model):
    __tablename__ = "periodos_academicos"

    id = db.Column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    nombre = db.Column(
        db.String(80),
        nullable=False,
        unique=True
    )

    fecha_inicio = db.Column(
        db.Date,
        nullable=False
    )

    fecha_fin = db.Column(
        db.Date,
        nullable=False
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    creado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    clases = db.relationship(
        "Clase",
        back_populates="periodo",
        lazy=True
    )

    def __repr__(self):
        return f"<PeriodoAcademico {self.nombre}>"


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    rol_id = db.Column(
        TINYINT(unsigned=True),
        db.ForeignKey("roles.id"),
        nullable=False
    )

    nombre = db.Column(
        db.String(80),
        nullable=False
    )

    apellido_paterno = db.Column(
        db.String(80),
        nullable=False
    )

    apellido_materno = db.Column(
        db.String(80),
        nullable=True
    )

    correo = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    ultimo_acceso = db.Column(
        db.DateTime,
        nullable=True
    )

    creado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    rol = db.relationship(
        "Rol",
        back_populates="usuarios"
    )

    alumno = db.relationship(
        "Alumno",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan"
    )

    profesor = db.relationship(
        "Profesor",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan"
    )

    @property
    def nombre_completo(self):
        partes = [
            self.nombre,
            self.apellido_paterno,
            self.apellido_materno
        ]

        return " ".join(
            parte for parte in partes if parte
        )

    @property
    def is_active(self):
        return self.activo

    def __repr__(self):
        return f"<Usuario {self.correo}>"


class Alumno(db.Model):
    __tablename__ = "alumnos"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    usuario_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("usuarios.id"),
        nullable=False,
        unique=True
    )

    carrera_id = db.Column(
        INTEGER(unsigned=True),
        db.ForeignKey("carreras.id"),
        nullable=False
    )

    matricula = db.Column(
        db.String(30),
        nullable=False,
        unique=True
    )

    cuatrimestre = db.Column(
        TINYINT(unsigned=True),
        nullable=False
    )

    creado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    usuario = db.relationship(
        "Usuario",
        back_populates="alumno"
    )

    carrera = db.relationship(
        "Carrera",
        back_populates="alumnos"
    )

    inscripciones = db.relationship(
        "Inscripcion",
        back_populates="alumno",
        lazy=True
    )

    materiales_asignados = db.relationship(
        "MaterialAlumno",
        back_populates="alumno",
        lazy=True
    )

    consultas_material = db.relationship(
        "ConsultaMaterial",
        back_populates="alumno",
        lazy=True
    )

    def __repr__(self):
        return f"<Alumno {self.matricula}>"


class Profesor(db.Model):
    __tablename__ = "profesores"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    usuario_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("usuarios.id"),
        nullable=False,
        unique=True
    )

    numero_empleado = db.Column(
        db.String(30),
        nullable=False,
        unique=True
    )

    especialidad = db.Column(
        db.String(150),
        nullable=True
    )

    creado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    usuario = db.relationship(
        "Usuario",
        back_populates="profesor"
    )

    clases_asignadas = db.relationship(
        "ClaseProfesor",
        back_populates="profesor",
        lazy=True
    )

    materiales = db.relationship(
        "Material",
        back_populates="profesor",
        lazy=True
    )

    def __repr__(self):
        return f"<Profesor {self.numero_empleado}>"


class Materia(db.Model):
    __tablename__ = "materias"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    clave = db.Column(
        db.String(30),
        nullable=False,
        unique=True
    )

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=True
    )

    activa = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    creado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    clases = db.relationship(
        "Clase",
        back_populates="materia",
        lazy=True
    )

    def __repr__(self):
        return f"<Materia {self.nombre}>"


class Clase(db.Model):
    __tablename__ = "clases"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    materia_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("materias.id"),
        nullable=False
    )

    periodo_id = db.Column(
        INTEGER(unsigned=True),
        db.ForeignKey("periodos_academicos.id"),
        nullable=False
    )

    codigo_clase = db.Column(
        db.String(30),
        nullable=False,
        unique=True
    )

    nombre_grupo = db.Column(
        db.String(50),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=True
    )

    activa = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    creado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    materia = db.relationship(
        "Materia",
        back_populates="clases"
    )

    periodo = db.relationship(
        "PeriodoAcademico",
        back_populates="clases"
    )

    profesores = db.relationship(
        "ClaseProfesor",
        back_populates="clase",
        cascade="all, delete-orphan",
        lazy=True
    )

    inscripciones = db.relationship(
        "Inscripcion",
        back_populates="clase",
        cascade="all, delete-orphan",
        lazy=True
    )

    materiales = db.relationship(
        "Material",
        back_populates="clase",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Clase {self.codigo_clase}>"


class ClaseProfesor(db.Model):
    __tablename__ = "clase_profesores"

    clase_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("clases.id"),
        primary_key=True
    )

    profesor_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("profesores.id"),
        primary_key=True
    )

    es_titular = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    asignado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    clase = db.relationship(
        "Clase",
        back_populates="profesores"
    )

    profesor = db.relationship(
        "Profesor",
        back_populates="clases_asignadas"
    )

    def __repr__(self):
        return f"<ClaseProfesor clase={self.clase_id} profesor={self.profesor_id}>"


class Inscripcion(db.Model):
    __tablename__ = "inscripciones"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    clase_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("clases.id"),
        nullable=False
    )

    alumno_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("alumnos.id"),
        nullable=False
    )

    estado = db.Column(
        ENUM(
            "ACTIVO",
            "BAJA",
            "FINALIZADO"
        ),
        nullable=False,
        default="ACTIVO"
    )

    inscrito_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    clase = db.relationship(
        "Clase",
        back_populates="inscripciones"
    )

    alumno = db.relationship(
        "Alumno",
        back_populates="inscripciones"
    )

    def __repr__(self):
        return f"<Inscripcion clase={self.clase_id} alumno={self.alumno_id}>"


class Material(db.Model):
    __tablename__ = "materiales"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    clase_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("clases.id"),
        nullable=False
    )

    profesor_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("profesores.id"),
        nullable=False
    )

    titulo = db.Column(
        db.String(200),
        nullable=False
    )

    descripcion_corta = db.Column(
        db.String(500),
        nullable=True
    )

    introduccion = db.Column(
        LONGTEXT,
        nullable=False
    )

    objetivo = db.Column(
        LONGTEXT,
        nullable=False
    )

    metodologia_trabajo = db.Column(
        LONGTEXT,
        nullable=False
    )

    detalles_material = db.Column(
        LONGTEXT,
        nullable=False
    )

    referencias_bibliograficas = db.Column(
        LONGTEXT,
        nullable=False
    )

    conclusion = db.Column(
        LONGTEXT,
        nullable=False
    )

    portada_ruta = db.Column(
        db.String(500),
        nullable=True
    )

    estado = db.Column(
        ENUM(
            "BORRADOR",
            "PUBLICADO",
            "ARCHIVADO"
        ),
        nullable=False,
        default="BORRADOR"
    )

    alcance = db.Column(
        ENUM(
            "TODA_LA_CLASE",
            "ALUMNOS_SELECCIONADOS"
        ),
        nullable=False,
        default="TODA_LA_CLASE"
    )

    permite_descarga = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    fecha_publicacion = db.Column(
        db.DateTime,
        nullable=True
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    creado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    clase = db.relationship(
        "Clase",
        back_populates="materiales"
    )

    profesor = db.relationship(
        "Profesor",
        back_populates="materiales"
    )

    alumnos_asignados = db.relationship(
        "MaterialAlumno",
        back_populates="material",
        cascade="all, delete-orphan",
        lazy=True
    )

    recursos = db.relationship(
        "RecursoMaterial",
        back_populates="material",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="RecursoMaterial.orden"
    )

    consultas = db.relationship(
        "ConsultaMaterial",
        back_populates="material",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Material {self.titulo}>"


class MaterialAlumno(db.Model):
    __tablename__ = "material_alumnos"

    material_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("materiales.id"),
        primary_key=True
    )

    alumno_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("alumnos.id"),
        primary_key=True
    )

    asignado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    material = db.relationship(
        "Material",
        back_populates="alumnos_asignados"
    )

    alumno = db.relationship(
        "Alumno",
        back_populates="materiales_asignados"
    )

    def __repr__(self):
        return f"<MaterialAlumno material={self.material_id} alumno={self.alumno_id}>"


class RecursoMaterial(db.Model):
    __tablename__ = "recursos_material"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    material_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("materiales.id"),
        nullable=False
    )

    tipo = db.Column(
        ENUM(
            "PDF",
            "IMAGEN",
            "VIDEO",
            "AUDIO",
            "DOCUMENTO",
            "PRESENTACION",
            "ENLACE"
        ),
        nullable=False
    )

    nombre_original = db.Column(
        db.String(255),
        nullable=False
    )

    ubicacion = db.Column(
        db.String(500),
        nullable=False
    )

    mime_type = db.Column(
        db.String(120),
        nullable=True
    )

    tamanio_bytes = db.Column(
        BIGINT(unsigned=True),
        nullable=True
    )

    texto_alternativo = db.Column(
        db.String(300),
        nullable=True
    )

    descripcion = db.Column(
        db.String(500),
        nullable=True
    )

    orden = db.Column(
        INTEGER(unsigned=True),
        nullable=False,
        default=1
    )

    creado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    material = db.relationship(
        "Material",
        back_populates="recursos"
    )

    def __repr__(self):
        return f"<RecursoMaterial {self.nombre_original}>"


class ConsultaMaterial(db.Model):
    __tablename__ = "consultas_material"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    material_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("materiales.id"),
        nullable=False
    )

    alumno_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey("alumnos.id"),
        nullable=False
    )

    primera_consulta = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    ultima_consulta = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    numero_consultas = db.Column(
        INTEGER(unsigned=True),
        nullable=False,
        default=1
    )

    material = db.relationship(
        "Material",
        back_populates="consultas"
    )

    alumno = db.relationship(
        "Alumno",
        back_populates="consultas_material"
    )

    def __repr__(self):
        return f"<ConsultaMaterial material={self.material_id} alumno={self.alumno_id}>"