from attr import define
from sqlalchemy import Boolean, Column, ForeignKey, Integer,String
from sqlalchemy.orm import relationship, Session

from .database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    flower_id = Column(Integer)


@define
class PurchaseCreate:
    user_id: int
    flower_id: int


class PurchasesRepository:

    def add_purchase(self, purchase: PurchaseCreate, db: Session) -> Purchase:
        db_purchase = Purchase(user_id=purchase.user_id, flower_id=purchase.flower_id)
        db.add(db_purchase)
        db.commit()
        db.refresh(db_purchase)
        return db_purchase

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> list[Purchase]:
        return db.query(Purchase).offset(skip).limit(limit).all()

    def get_by_user_id(self, user_id: int, db: Session):
        return db.query(Purchase).filter(Purchase.user_id==user_id).all()