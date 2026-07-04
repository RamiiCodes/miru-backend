from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.user import User


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str) -> User:
    user = User(email=email)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def create_user_with_password(
    db: Session,
    email: str,
    password_hash: str,
) -> User:
    user = User(
        email=email,
        password_hash=password_hash,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user