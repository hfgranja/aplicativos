"""Popula o banco com um usuário administrador e dados de exemplo.

Uso:
    python seed.py
"""
from datetime import date

from database import SessionLocal, engine, Base
import models
from auth import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    admin_email = "diretoria@escola.sp.gov.br"
    admin = db.query(models.User).filter(models.User.email == admin_email).first()
    if not admin:
        admin = models.User(
            name="Direção",
            email=admin_email,
            password_hash=hash_password("mudar123"),
            role="vice_diretor",
        )
        db.add(admin)
        db.commit()
        print(f"Usuário criado: {admin_email} / senha: mudar123")
    else:
        print("Usuário admin já existe.")

    if db.query(models.SchoolClass).count() == 0:
        turma = models.SchoolClass(
            name="6º A",
            grade_level="6º ano EF",
            shift="manhã",
            school_year=date.today().year,
        )
        db.add(turma)
        db.commit()
        db.refresh(turma)

        alunos = [
            models.Student(
                name="Ana Souza",
                ra="123456-SP",
                class_id=turma.id,
                guardian_name="Maria Souza",
                guardian_phone="(11) 99999-0001",
            ),
            models.Student(
                name="Bruno Lima",
                ra="123457-SP",
                class_id=turma.id,
                guardian_name="José Lima",
                guardian_phone="(11) 99999-0002",
            ),
        ]
        db.add_all(alunos)

        professor = models.Teacher(
            name="Carla Mendes",
            email="carla.mendes@escola.sp.gov.br",
            subjects="Língua Portuguesa",
        )
        db.add(professor)
        db.commit()
        db.refresh(professor)

        db.add(
            models.TeacherAssignment(
                teacher_id=professor.id,
                class_id=turma.id,
                subject="Língua Portuguesa",
            )
        )
        db.commit()
        print("Dados de exemplo criados: 1 turma, 2 alunos, 1 professor.")
    else:
        print("Já existem turmas cadastradas, pulando dados de exemplo.")
finally:
    db.close()
