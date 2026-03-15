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
    transcript: Optional[str]
    feedback_raw: Optional[str]
    feedback_generated_at: Optional[datetime]
    cnv_script: Optional[str]
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
