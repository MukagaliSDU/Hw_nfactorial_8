from attr import define
from sqlalchemy import Boolean, Column, ForeignKey, Integer,String
from sqlalchemy.orm import relationship, Session

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    password = Column(String)


@define
class UserCreate:
    email: str
    fullname: str
    password: str


class UsersRepository:

    def create_user(self, db: Session,  user: UserCreate) -> User:
        db_user = User(email=user.email, password=user.password, full_name=user.fullname)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def get_user(self, db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        return db.query(User).offset(skip).limit(limit).all()


