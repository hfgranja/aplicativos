from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
import models  # noqa: F401 (garante que os modelos sejam registrados antes do create_all)
from routers import (
    auth,
    students,
    classes,
    teachers,
    attendance,
    grades,
    occurrences,
    announcements,
    dashboard,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gestão Escolar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(classes.router)
app.include_router(teachers.router)
app.include_router(attendance.router)
app.include_router(grades.router)
app.include_router(occurrences.router)
app.include_router(announcements.router)
app.include_router(dashboard.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
