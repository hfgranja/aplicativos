from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Auth / Users ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "coordenador"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    email: str
    role: str
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Classes ----------
class SchoolClassCreate(BaseModel):
    name: str
    grade_level: Optional[str] = None
    shift: Optional[str] = None
    school_year: Optional[int] = None


class SchoolClassOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    grade_level: Optional[str] = None
    shift: Optional[str] = None
    school_year: int
    student_count: int = 0


# ---------- Students ----------
class StudentCreate(BaseModel):
    name: str
    ra: Optional[str] = None
    birth_date: Optional[date] = None
    class_id: Optional[str] = None
    status: str = "ativo"
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    ra: Optional[str] = None
    birth_date: Optional[date] = None
    class_id: Optional[str] = None
    status: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    ra: Optional[str] = None
    birth_date: Optional[date] = None
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    status: str
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None
    notes: Optional[str] = None


# ---------- Teachers ----------
class TeacherCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    subjects: Optional[str] = None
    status: str = "ativo"


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    subjects: Optional[str] = None
    status: Optional[str] = None


class TeacherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    subjects: Optional[str] = None
    status: str


class AssignmentCreate(BaseModel):
    teacher_id: str
    class_id: str
    subject: str


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    teacher_id: str
    teacher_name: Optional[str] = None
    class_id: str
    class_name: Optional[str] = None
    subject: str


# ---------- Attendance ----------
class AttendanceEntry(BaseModel):
    student_id: str
    present: bool = True
    justified: bool = False
    notes: Optional[str] = None


class AttendanceBulkCreate(BaseModel):
    class_id: str
    date: date
    entries: List[AttendanceEntry]


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    student_id: str
    student_name: Optional[str] = None
    class_id: str
    date: date
    present: bool
    justified: bool
    notes: Optional[str] = None


# ---------- Grades ----------
class GradeCreate(BaseModel):
    student_id: str
    subject: str
    term: int
    school_year: Optional[int] = None
    value: float
    notes: Optional[str] = None


class GradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    student_id: str
    student_name: Optional[str] = None
    subject: str
    term: int
    school_year: int
    value: float
    notes: Optional[str] = None


# ---------- Occurrences ----------
class OccurrenceCreate(BaseModel):
    student_id: str
    date: Optional[date] = None
    type: str = "disciplinar"
    description: str
    action_taken: Optional[str] = None
    guardian_notified: bool = False


class OccurrenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    student_id: str
    student_name: Optional[str] = None
    date: date
    type: str
    description: str
    action_taken: Optional[str] = None
    guardian_notified: bool
    reported_by: Optional[str] = None
    reported_by_name: Optional[str] = None
    created_at: datetime


# ---------- Announcements ----------
class AnnouncementCreate(BaseModel):
    title: str
    body: str
    class_id: Optional[str] = None


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    body: str
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    created_by: Optional[str] = None
    created_by_name: Optional[str] = None
    created_at: datetime


# ---------- Dashboard ----------
class DashboardStats(BaseModel):
    total_students_active: int
    total_teachers_active: int
    total_classes: int
    attendance_rate_today: Optional[float] = None
    recent_occurrences: List[OccurrenceOut] = []
    recent_announcements: List[AnnouncementOut] = []
