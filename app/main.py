
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth.routes import router as auth_router
from app.users.routes import router as users_router
from app.tutoring.routes import router as tutoring_router
from app.exams.routes import router as exams_router
from app.rag.routes import router as rag_router

app = FastAPI(
    title="Ustadih RAG - Educational AI Tutor",
    description="AI-powered tutoring system for Iraqi students using RAG technology",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(tutoring_router, prefix="/tutoring", tags=["tutoring"])
app.include_router(exams_router, prefix="/exams", tags=["exams"])
app.include_router(rag_router, prefix="/rag", tags=["rag"])


@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "app": "Ustadih RAG - Educational AI Tutor",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": "/auth",
            "users": "/users",
            "tutoring": "/tutoring",
            "exams": "/exams",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
def health_check():
    """System health check."""
    return {"status": "healthy", "message": "Ustadih RAG API is operational"}
