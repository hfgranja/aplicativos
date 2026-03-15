from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_tables
from routers import teachers, observations, media, llm, analytics, knowledge, action_results

app = FastAPI(title="PEC Teacher Feedback", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(teachers.router)
app.include_router(observations.router)
app.include_router(media.router)
app.include_router(llm.router)
app.include_router(analytics.router)
app.include_router(knowledge.router)
app.include_router(action_results.router)


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/")
def root():
    return {"message": "PEC Teacher Feedback API", "version": "1.0.0"}
