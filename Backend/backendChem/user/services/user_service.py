from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status  
from auth.utils.auth_utils import get_password_hash
from user.models.user import User
from user.schemas.user import UserCreate


def get_users(db: Session):
    return db.query(User).all()


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    # 🔎 1. Cek dulu username sudah dipakai atau belum
    existing_by_username = (
        db.query(User)
        .filter(User.username == user.username)
        .first()
    )
    if existing_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username sudah terdaftar.",
        )

    # 🔎 2. Cek email sudah dipakai atau belum
    existing_by_email = (
        db.query(User)
        .filter(User.email == str(user.email))
        .first()
    )
    if existing_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar.",
        )

    # ✅ 3. Kalau aman, baru insert
    db_user = User(
        email=str(user.email),
        username=user.username,
        password=get_password_hash(user.password),
    )

    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        return db_user

    except IntegrityError:
        # jaga-jaga kalau ada race condition
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User dengan username atau email ini sudah terdaftar.",
        )


def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return
