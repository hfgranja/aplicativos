import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Date, Text
from sqlalchemy.orm import relationship
from database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    school = Column(String)
    subject = Column(String)
    grade = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    observations = relationship("Observation", back_populates="teacher", cascade="all, delete")


class MediaFile(Base):
    __tablename__ = "media_files"
    id = Column(String, primary_key=True, default=gen_uuid)
    original_name = Column(String)
    stored_name = Column(String)
    mime_type = Column(String)
    file_size_bytes = Column(Integer)
    transcript = Column(Text)
    transcribed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


RATING = "TEXT"  # nao_observado | insuficiente | adequado | muito_bom


class Observation(Base):
    __tablename__ = "observations"
    id = Column(String, primary_key=True, default=gen_uuid)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    media_file_id = Column(String, ForeignKey("media_files.id"), nullable=True)
    observed_at = Column(DateTime, nullable=False)
    pec_name = Column(String)
    focus_area = Column(String)

    # Section 1 – Planejamento e Alinhamento Curricular
    s1_c1 = Column(String)  # alinhado ao Currículo Paulista
    s1_c2 = Column(String)  # objetivos explícitos
    s1_c3 = Column(String)  # habilidades adequadas ao ano
    s1_c4 = Column(String)  # atividades coerentes com objetivos

    # Section 2 – Condução Didática
    s2_c1 = Column(String)  # início nos 5 primeiros minutos
    s2_c2 = Column(String)  # retomada de conhecimentos prévios
    s2_c3 = Column(String)  # explicação clara com exemplos
    s2_c4 = Column(String)  # variedade metodológica
    s2_c5 = Column(String)  # perguntas para verificar compreensão
    s2_c6 = Column(String)  # fechamento/síntese
    s2_methodologies = Column(Text)  # JSON array

    # Section 3 – Gestão da Aprendizagem
    s3_c1 = Column(String)  # engajamento e participação
    s3_c2 = Column(String)  # identifica e atende dificuldades
    s3_c3 = Column(String)  # diferenciação pedagógica
    s3_c4 = Column(String)  # avaliação formativa
    s3_c5 = Column(String)  # feedback aos alunos

    # Section 4 – Materiais e Recursos
    s4_c1 = Column(String)  # materiais oficiais SEDUC
    s4_c2 = Column(String)  # recursos disponíveis
    s4_c3 = Column(String)  # tempo bem distribuído
    s4_c4 = Column(String)  # registros claros e organizados

    # Section 5 – Clima e Postura
    s5_c1 = Column(String)  # ambiente de respeito
    s5_c2 = Column(String)  # boa relação com alunos
    s5_c3 = Column(String)  # manejo de indisciplina
    s5_c4 = Column(String)  # preparo prévio e organização
    s5_c5 = Column(String)  # postura profissional

    # Narrative (PEC)
    habilidades_curriculo = Column(Text)
    pontos_fortes = Column(Text)        # JSON array
    focos_desenvolvimento = Column(Text)  # JSON array
    sugestoes = Column(Text)

    # Teacher self-reflection
    teacher_feeling = Column(Text)
    teacher_comments = Column(Text)
    teacher_expectations = Column(Text)
    teacher_commitment = Column(Text)

    # References
    bncc_skills = Column(Text)           # JSON array of skill codes
    seduc_materials = Column(Text)
    next_observation_date = Column(Date)
    next_observation_focus = Column(Text)
    combined_actions = Column(Text)      # JSON array

    # LLM outputs
    transcript = Column(Text)
    feedback_raw = Column(Text)          # JSON from LLM
    feedback_generated_at = Column(DateTime)
    cnv_script = Column(Text)            # JSON CNV script

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="observations")
