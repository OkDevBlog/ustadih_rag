
from fastapi import APIRouter, Request, Depends
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.db.models import User
from app.auth.google_oauth import oauth

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    user = db.query(User).filter(User.email == user_info["email"]).first()
    if not user:
        user = User(
            id=user_info["sub"],
            email=user_info["email"],
            full_name=user_info["name"],
            google_id=user_info["sub"],
            is_active=True
        )
        db.add(user)
        db.commit()

    access_token = create_access_token({"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}
