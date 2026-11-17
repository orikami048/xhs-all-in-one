from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import decode_token
from backend.app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if token:
        try:
            payload = decode_token(token)
            if payload.get("token_type") == "access":
                user = db.get(User, payload.get("user_id"))
                if user is not None:
                    return user
        except Exception:
            pass

    # 免登录模式：无 Token 或 Token 无效时直接自动使用本地默认用户
    user = db.query(User).order_by(User.id).first()
    if user is None:
        user = User(username="admin", is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
