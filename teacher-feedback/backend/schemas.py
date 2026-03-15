from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


# ---- Teacher ----
class TeacherCreate(BaseModel):
    name: str
    school: Optional[str] = None
    subject: Optional[str] = None
    grade: Optional[str] = None


class TeacherOut(BaseModel):
    id: str
    name: str
    school: Optional[str]
    subject: Optional[str]
    grade: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Observation ----
class ObservationCreate(BaseModel):
    teacher_id: str
    media_file_id: Optional[str] = None
    observed_at: datetime
    pec_name: Optional[str] = None
    focus_area: Optional[str] = None
    # Section 1
    s1_c1: Optional[str] = None
    s1_c2: Optional[str] = None
    s1_c3: Optional[str] = None
    s1_c4: Optional[str] = None
    # Section 2
    s2_c1: Optional[str] = None
    s2_c2: Optional[str] = None
    s2_c3: Optional[str] = None
    s2_c4: Optional[str] = None
    s2_c5: Optional[str] = None
    s2_c6: Optional[str] = None
    s2_methodologies: Optional[str] = None  # JSON
    # Section 3
    s3_c1: Optional[str] = None
    s3_c2: Optional[str] = None
    s3_c3: Optional[str] = None
    s3_c4: Optional[str] = None
    s3_c5: Optional[str] = None
    # Section 4
    s4_c1: Optional[str] = None
    s4_c2: Optional[str] = None
    s4_c3: Optional[str] = None
    s4_c4: Optional[str] = None
    # Section 5
    s5_c1: Optional[str] = None
    s5_c2: Optional[str] = None
    s5_c3: Optional[str] = None
    s5_c4: Optional[str] = None
    s5_c5: Optional[str] = None
    # Narrative
    habilidades_curriculo: Optional[str] = None
    pontos_fortes: Optional[str] = None
    focos_desenvolvimento: Optional[str] = None
    sugestoes: Optional[str] = None
    # EF I – Domínio de Conteúdo
    ef1_dc_c1: Optional[str] = None
    ef1_dc_c2: Optional[str] = None
    ef1_dc_c3: Optional[str] = None
    # EF I – Engajamento dos Estudantes
    ef1_es_c1: Optional[str] = None
    ef1_es_c2: Optional[str] = None
    ef1_es_c3: Optional[str] = None
    # EF I – Metodologias e Estratégias
    ef1_me_c1: Optional[str] = None
    ef1_me_c2: Optional[str] = None
    ef1_me_c3: Optional[str] = None
    # EF I – Material Didático
    ef1_md_c1: Optional[str] = None
    ef1_md_c2: Optional[str] = None
    ef1_md_c3: Optional[str] = None
    # EF I – Gestão de Sala
    ef1_gs_c1: Optional[str] = None
    ef1_gs_c2: Optional[str] = None
    ef1_gs_c3: Optional[str] = None
    # EF I – Manejo de Conflitos
    ef1_mc_c1: Optional[str] = None
    ef1_mc_c2: Optional[str] = None
    ef1_mc_c3: Optional[str] = None
    # EF I – Sugestões e Encaminhamentos
    ef1_sugestoes: Optional[str] = None
    ef1_encaminhamentos: Optional[str] = None  # JSON array
    # Teacher reflection
    teacher_feeling: Optional[str] = None
    teacher_comments: Optional[str] = None
    teacher_expectations: Optional[str] = None
    teacher_commitment: Optional[str] = None
    # References
    bncc_skills: Optional[str] = None
    seduc_materials: Optional[str] = None
    next_observation_date: Optional[date] = None
    next_observation_focus: Optional[str] = None
    combined_actions: Optional[str] = None


class ObservationOut(ObservationCreate):
    id: str
    transcript: Optional[str] = None
    feedback_raw: Optional[str] = None
    feedback_generated_at: Optional[datetime] = None
    cnv_script: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Media ----
class MediaFileOut(BaseModel):
    id: str
    original_name: str
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    transcript: Optional[str]
    transcribed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ---- LLM ----
class CNVRequest(BaseModel):
    questions: List[str]


# ---- Action Plan Results ----
class ActionResultCreate(BaseModel):
    observation_id: str
    teacher_id: str
    action_text: str
    action_type: str  # 'combined' | 'ef1_encaminhamento'
    deadline: Optional[date] = None
    responsible: Optional[str] = None


class ActionResultUpdate(BaseModel):
    status: str  # pendente | realizado | parcial
    result_notes: Optional[str] = None


class ActionResultOut(BaseModel):
    id: str
    observation_id: str
    teacher_id: str
    action_text: str
    action_type: str
    deadline: Optional[date]
    responsible: Optional[str]
    status: str
    result_notes: Optional[str]
    score_before: Optional[int]
    score_after: Optional[int]
    delta_score: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
