from attr import define
from sqlalchemy import Boolean, Column, ForeignKey, Integer,String
from sqlalchemy.orm import relationship, Session

from .database import Base

from pydantic import BaseModel


class Flower(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    count = Column(Integer)
    cost = Column(Integer)


@define
class FlowerCreate: # use when create and update flowers
    name: str
    count: int
    cost: int


class Response_Flower(BaseModel):
    name: str
    cost: int

class FlowersRepository:
    def create_flower(self, flower: FlowerCreate, db: Session) -> Flower:
        db_flower = Flower(name=flower.name, cost=flower.cost, count=flower.count)
        db.add(db_flower)
        db.commit()
        db.refresh(db_flower)
        return db_flower

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> list[Flower]:
        return db.query(Flower).offset(skip).limit(limit).all()

    def get_flower_by_id(self, db: Session, flower_id: int) -> Flower:
        return db.query(Flower).filter(Flower.id == flower_id).first()

    def get_flowers_list(self, flowers_id, db: Session) -> list[Flower]:
        res = []
        if flowers_id is None:
            return res
        for id in flowers_id:
            if id.isdigit():
                res.append(self.get_flower_by_id(db=db, flower_id=id))
        return res

    def get_response_flowers(self, flowers_id: list, db: Session) -> list[Response_Flower]:
        res = []
        if flowers_id is None:
            return res
        for id in flowers_id:
            db_flower = self.get_flower_by_id(db=db, flower_id=id.flower_id)
            res.append(Response_Flower(name=db_flower.name, cost=db_flower.cost))
        return res

    def update_flowers(self, flower_id: int, flower: FlowerCreate, db: Session):
        db_flower = self.get_flower_by_id(flower_id=flower_id, db=db)
        db_flower.name = flower.name
        db_flower.count = flower.count
        db_flower.cost = flower.cost
        db.commit()
        db.refresh(db_flower)
        return db_flower

    def delete_flower(self, flower_id: int, db: Session):
        db_flower = self.get_flower_by_id(db=db, flower_id=flower_id)
        db.delete(db_flower)
        db.commit()
        return None










