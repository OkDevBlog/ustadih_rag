
"""Authentication routes for Google OAuth and JWT token management."""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from starlette.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import uuid

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.db.models import User
from app.auth.google_oauth import oauth
from app.schemas import TokenResponse, HealthResponse

router = APIRouter()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/ping", response_model=HealthResponse)
def ping():
    """Health check endpoint."""
    return {"status": "ok", "message": "Auth service is running"}


@router.get("/google/login")
async def google_login(request: Request):
    """
    Initiate Google OAuth login flow.
    Redirects user to Google authentication page.
    """
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.
    Creates or updates user and returns JWT token.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        # Check if user already exists
        user = db.query(User).filter(User.email == user_info["email"]).first()
        
        if not user:
            # Create new user from Google info
            user = User(
                id=f"user_{uuid.uuid4().hex[:12]}",
                email=user_info["email"],
                full_name=user_info.get("name"),
                google_id=user_info["sub"],
                is_active=True
            )
            db.add(user)
            db.commit()
        else:
            # Update Google ID if not set
            if not user.google_id:
                user.google_id = user_info["sub"]
                db.commit()

        # Create access token
        access_token = create_access_token({"sub": user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/token", response_model=TokenResponse)
async def get_token(user_id: str, db: Session = Depends(get_db)):
    """
    Get access token for a user (for testing purposes).
    In production, use OAuth flow instead.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    access_token = create_access_token({"sub": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
