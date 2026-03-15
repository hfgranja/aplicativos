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


class Observation(Base):
    __tablename__ = "observations"
    id = Column(String, primary_key=True, default=gen_uuid)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    media_file_id = Column(String, ForeignKey("media_files.id"), nullable=True)
    observed_at = Column(DateTime, nullable=False)
    pec_name = Column(String)
    focus_area = Column(String)

    # Section 1 – Planejamento e Alinhamento Curricular
    s1_c1 = Column(String)
    s1_c2 = Column(String)
    s1_c3 = Column(String)
    s1_c4 = Column(String)

    # Section 2 – Condução Didática
    s2_c1 = Column(String)
    s2_c2 = Column(String)
    s2_c3 = Column(String)
    s2_c4 = Column(String)
    s2_c5 = Column(String)
    s2_c6 = Column(String)
    s2_methodologies = Column(Text)  # JSON array

    # Section 3 – Gestão da Aprendizagem
    s3_c1 = Column(String)
    s3_c2 = Column(String)
    s3_c3 = Column(String)
    s3_c4 = Column(String)
    s3_c5 = Column(String)

    # Section 4 – Materiais e Recursos
    s4_c1 = Column(String)
    s4_c2 = Column(String)
    s4_c3 = Column(String)
    s4_c4 = Column(String)

    # Section 5 – Clima e Postura
    s5_c1 = Column(String)
    s5_c2 = Column(String)
    s5_c3 = Column(String)
    s5_c4 = Column(String)
    s5_c5 = Column(String)

    # Narrative (PEC)
    habilidades_curriculo = Column(Text)
    pontos_fortes = Column(Text)          # JSON array
    focos_desenvolvimento = Column(Text)  # JSON array
    sugestoes = Column(Text)

    # EF I – Domínio de Conteúdo (Pedro Demo: "Ser professor é qualidade")
    ef1_dc_c1 = Column(String)  # Conhecimento sólido do conteúdo
    ef1_dc_c2 = Column(String)  # Explicações adequadas à faixa etária
    ef1_dc_c3 = Column(String)  # Relações com cotidiano das crianças

    # EF I – Engajamento dos Estudantes (Pedro Demo: "Educar pela pesquisa")
    ef1_es_c1 = Column(String)  # Interesse, curiosidade e participação
    ef1_es_c2 = Column(String)  # Professor valoriza falas e produções
    ef1_es_c3 = Column(String)  # Clima de ludicidade e pertencimento

    # EF I – Metodologias e Estratégias (Pedro Demo: "Avaliação qualitativa")
    ef1_me_c1 = Column(String)  # Abordagens variadas e adequadas para EF I
    ef1_me_c2 = Column(String)  # Estimula pensamento e autonomia
    ef1_me_c3 = Column(String)  # Equilibra momentos coletivos, duplas e individuais

    # EF I – Material Didático
    ef1_md_c1 = Column(String)  # Materiais concretos/manipuláveis utilizados
    ef1_md_c2 = Column(String)  # Recursos adequados à faixa etária
    ef1_md_c3 = Column(String)  # Usa materiais oficiais intencionalmente

    # EF I – Gestão de Sala
    ef1_gs_c1 = Column(String)  # Espaço físico favorece aprendizagem
    ef1_gs_c2 = Column(String)  # Rotinas e transições bem gerenciadas
    ef1_gs_c3 = Column(String)  # Tempo produtivo, pouco tempo ocioso

    # EF I – Manejo de Conflitos
    ef1_mc_c1 = Column(String)  # Intervém com calma e assertividade
    ef1_mc_c2 = Column(String)  # Estratégias restaurativas e dialógicas
    ef1_mc_c3 = Column(String)  # Mantém ambiente acolhedor

    # EF I – Sugestões e Encaminhamentos
    ef1_sugestoes = Column(Text)         # Texto livre de sugestões
    ef1_encaminhamentos = Column(Text)   # JSON array [{encaminhamento, responsible, deadline, status}]

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


class KnowledgeBase(Base):
    """Indexed extracts from observations for RAG context in future feedbacks."""
    __tablename__ = "knowledge_base"
    id = Column(String, primary_key=True, default=gen_uuid)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    observation_id = Column(String, ForeignKey("observations.id"), nullable=False)
    source_type = Column(String)   # 'feedback' | 'action_plan' | 'transcript' | 'best_practice'
    subject = Column(String)       # e.g. "Matemática"
    grade_band = Column(String)    # 'ef1' | 'ef2' | 'em'
    content = Column(Text)         # Indexed text
    score_at_time = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class ActionPlanResult(Base):
    """Tracks execution and outcome of each combined action / encaminhamento."""
    __tablename__ = "action_plan_results"
    id = Column(String, primary_key=True, default=gen_uuid)
    observation_id = Column(String, ForeignKey("observations.id"), nullable=False)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    action_text = Column(Text)
    action_type = Column(String)   # 'combined' | 'ef1_encaminhamento'
    deadline = Column(Date)
    responsible = Column(String)   # professor | escola | família | rede
    status = Column(String, default="pendente")  # pendente | realizado | parcial
    result_notes = Column(Text)
    score_before = Column(Integer)
    score_after = Column(Integer)
    delta_score = Column(Integer)
    next_observation_id = Column(String, ForeignKey("observations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
