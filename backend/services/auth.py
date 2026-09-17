import os
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.database import get_db
from backend.models.models import User

security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        # Fallback guest user for seamless public viewing if unauthenticated
        guest = db.query(User).filter_by(username="guest_viewer").first()
        if not guest:
            guest = User(
                username="guest_viewer",
                email="guest@nirvana.gov.in",
                hashed_password=hash_password("guest_pass"),
                role="VIEWER",
                full_name="Guest Viewer"
            )
            db.add(guest)
            db.commit()
            db.refresh(guest)
        return guest

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {allowed_roles}. Current role: {current_user.role}"
            )
        return current_user
    return role_checker

def seed_default_users(db: Session):
    defaults = [
        {"username": "admin", "email": "admin@nirvana.gov.in", "role": "ADMIN", "name": "System Administrator", "pass": "NirvanaAdmin2026!"},
        {"username": "officer", "email": "officer@nirvana.gov.in", "role": "OFFICER", "name": "Nodal Verification Officer", "pass": "NirvanaOfficer2026!"},
        {"username": "analyst", "email": "analyst@nirvana.gov.in", "role": "ANALYST", "name": "Vigilance Data Analyst", "pass": "NirvanaAnalyst2026!"},
        {"username": "viewer", "email": "viewer@nirvana.gov.in", "role": "VIEWER", "name": "Public Oversight Viewer", "pass": "NirvanaViewer2026!"},
    ]
    for u in defaults:
        if not db.query(User).filter_by(username=u["username"]).first():
            user = User(
                username=u["username"],
                email=u["email"],
                role=u["role"],
                full_name=u["name"],
                hashed_password=hash_password(u["pass"])
            )
            db.add(user)
    db.commit()
