
"""Authentication routes for Google OAuth and JWT token management."""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from starlette.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import uuid

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import SessionLocal
from app.db.models import User
from app.auth.google_oauth import oauth
from app.schemas import TokenResponse, HealthResponse, UserCreate, LoginRequest

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
        "token_type": "bearer",
        "user_id": user.id
    }


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with email and password."""
    # Validate input
    if not user.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required")

    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed = hash_password(user.password)

    new_user = User(
        id=user_id,
        email=user.email,
        hashed_password=hashed,
        full_name=user.full_name,
        is_active=True
    )
    db.add(new_user)
    db.commit()

    access_token = create_access_token({"sub": new_user.id})
    return {"access_token": access_token, "token_type": "bearer", "user_id": new_user.id}


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password and receive JWT token."""
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}
