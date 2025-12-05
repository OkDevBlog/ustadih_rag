
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.users.routes import router as users_router
from app.tutoring.routes import router as tutoring_router
from app.exams.routes import router as exams_router

app = FastAPI(title="Iraq AI Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(tutoring_router, prefix="/tutoring", tags=["tutoring"])
app.include_router(exams_router, prefix="/exams", tags=["exams"])
