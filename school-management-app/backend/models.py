import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Date,
    ForeignKey,
    Integer,
    Float,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship
from database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    """Membro da equipe gestora (diretor, vice-diretor, coordenador, secretaria)."""

    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="coordenador")
    created_at = Column(DateTime, default=datetime.utcnow)


class SchoolClass(Base):
    """Turma."""

    __tablename__ = "classes"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)  # ex: "6º A"
    grade_level = Column(String)  # ex: "6º ano EF"
    shift = Column(String)  # manhã | tarde | noite
    school_year = Column(Integer, nullable=False, default=lambda: date.today().year)
    created_at = Column(DateTime, default=datetime.utcnow)

    students = relationship("Student", back_populates="school_class")
    assignments = relationship(
        "TeacherAssignment", back_populates="school_class", cascade="all, delete"
    )


class Student(Base):
    """Aluno."""

    __tablename__ = "students"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    ra = Column(String)  # Registro do Aluno (RA - SED SP)
    birth_date = Column(Date)
    class_id = Column(String, ForeignKey("classes.id"), nullable=True)
    status = Column(String, nullable=False, default="ativo")  # ativo|transferido|evadido
    guardian_name = Column(String)
    guardian_phone = Column(String)
    guardian_email = Column(String)
    address = Column(String)
    enrollment_date = Column(Date, default=date.today)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    school_class = relationship("SchoolClass", back_populates="students")
    attendances = relationship(
        "Attendance", back_populates="student", cascade="all, delete"
    )
    grades = relationship("Grade", back_populates="student", cascade="all, delete")
    occurrences = relationship(
        "Occurrence", back_populates="student", cascade="all, delete"
    )


class Teacher(Base):
    """Professor."""

    __tablename__ = "teachers"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    subjects = Column(String)  # lista separada por vírgula
    status = Column(String, nullable=False, default="ativo")  # ativo|afastado|desligado
    created_at = Column(DateTime, default=datetime.utcnow)

    assignments = relationship(
        "TeacherAssignment", back_populates="teacher", cascade="all, delete"
    )


class TeacherAssignment(Base):
    """Atribuição de aula: professor + turma + disciplina."""

    __tablename__ = "teacher_assignments"
    id = Column(String, primary_key=True, default=gen_uuid)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    class_id = Column(String, ForeignKey("classes.id"), nullable=False)
    subject = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="assignments")
    school_class = relationship("SchoolClass", back_populates="assignments")


class Attendance(Base):
    """Registro de frequência de um aluno em uma data."""

    __tablename__ = "attendance"
    id = Column(String, primary_key=True, default=gen_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    class_id = Column(String, ForeignKey("classes.id"), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    present = Column(Boolean, nullable=False, default=True)
    justified = Column(Boolean, nullable=False, default=False)
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="attendances")


class Grade(Base):
    """Nota de um aluno em uma disciplina/bimestre."""

    __tablename__ = "grades"
    id = Column(String, primary_key=True, default=gen_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    subject = Column(String, nullable=False)
    term = Column(Integer, nullable=False)  # bimestre 1-4
    school_year = Column(Integer, nullable=False, default=lambda: date.today().year)
    value = Column(Float, nullable=False)
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="grades")


class Occurrence(Base):
    """Ocorrência disciplinar, elogio, saúde etc."""

    __tablename__ = "occurrences"
    id = Column(String, primary_key=True, default=gen_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    type = Column(String, nullable=False, default="disciplinar")  # disciplinar|elogio|saude|outro
    description = Column(Text, nullable=False)
    action_taken = Column(Text)
    reported_by = Column(String, ForeignKey("users.id"), nullable=True)
    guardian_notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="occurrences")


class Announcement(Base):
    """Comunicado interno (para uma turma específica ou geral)."""

    __tablename__ = "announcements"
    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    class_id = Column(String, ForeignKey("classes.id"), nullable=True)  # null = geral
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
