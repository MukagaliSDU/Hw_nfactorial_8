import json
from jose import jwt

from fastapi import Cookie, FastAPI, Form, Request, Response, templating, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from pydantic import BaseModel

from .database import Base, engine, SessionLocal
from .users_repository import User, UsersRepository, UserCreate
from .flowers_repository import Flower, FlowerCreate, FlowersRepository
from .purchases_repository import Purchase, PurchaseCreate, PurchasesRepository

Base.metadata.create_all(bind=engine)

app = FastAPI()
oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")

users_repo = UsersRepository()
flowers_repository = FlowersRepository()
purchases_repository = PurchasesRepository()


class ReadUserResponse(BaseModel):
    id: int
    email: str
    full_name: str


class FlowerUpdateResponse(BaseModel):
    name: str
    count: int
    cost: int


@app.get("/")
def root(request: Request):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def encode(user_id: str) -> str:
    json_user = {"user_id": user_id}
    encode_user = jwt.encode(json_user, "nfactorial", "HS256")
    return encode_user


def decode(token: str) -> int:
    data = jwt.decode(token, "nfactorial", "HS256")
    return data["user_id"]


@app.post("/signup")
def post_sign_up(
    email: str = Form(),
    full_name: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
):
    user = UserCreate(email=email, fullname=full_name, password=password)
    users_repo.create_user(db=db, user=user)
    return Response(status_code=200)


@app.post('/login')
def post_login(username: str = Form(), password: str = Form(), db: Session = Depends(get_db)):

    user = users_repo.get_user_by_email(db, username)
    if user is None:
        raise HTTPException(status_code=401, detail={"username": username, "msg": "we don't have such a user"})
    elif user.password == password:
        token = encode(str(user.id))
        return{
            "access_token": token,
            "type": "bearer",
        }


@app.get("/profile", response_model=ReadUserResponse)
def get_profile(token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = decode(token)
    db_user = users_repo.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return db_user


@app.get("/flowers")
def get_flowers(db: Session = Depends(get_db)):
    return flowers_repository.get_all(db=db)


@app.post("/flowers")
def post_flowers(
        name: str = Form(),
        count: int = Form(),
        cost: int = Form(),
        token: str = Depends(oauth2_schema),
        db: Session = Depends(get_db)
):
    flower = FlowerCreate(name=name, count=count, cost=cost)
    db_flower = flowers_repository.create_flower(flower=flower, db=db)

    return{
        "id": db_flower.id
    }


@app.patch("/flowers/{flower_id}")
def update_flower(
        flower_id: int,
        flower_update: FlowerUpdateResponse,
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_schema)
):
    db_flower = flowers_repository.get_flower_by_id(db=db, flower_id=flower_id)
    if db_flower is None:
        raise HTTPException(status_code=404, detail="Flower not found")
    flowers_repository.update_flowers(db=db, flower_id=flower_id, flower=flower_update)
    return Response(status_code=200)


@app.delete("/flowers/{flower_id}")
def delete_flower(flower_id: int, db: Session = Depends(get_db), token:str = Depends(oauth2_schema)):
    db_flower = flowers_repository.get_flower_by_id(db=db, flower_id=flower_id)
    if db_flower is None:
        raise HTTPException(status_code=404, detail="Flower not found")
    flowers_repository.delete_flower(db=db, flower_id=flower_id)
    return Response(status_code=200)


@app.post("/cart/items")
def post_items(
        request: Request,
        flower_id: int = Form(),
        token: str = Depends(oauth2_schema),
        cart: str = Cookie(default="[]"),
        db: Session = Depends(get_db)
):
    cart_token = request.cookies.get(token)
    if cart_token is None:
        cart_token = cart
    cart_json = json.loads(cart_token)
    response = Response(status_code=200)
    flower = flowers_repository.get_flower_by_id(db=db, flower_id=flower_id)
    if flower is not None:
        cart_json.append(flower_id)
        new_json = json.dumps(cart_json)
        response.set_cookie(key=token, value=new_json)
    else:
        raise HTTPException(status_code=404, detail={"value": flower_id, "msg": "ooops we have not this flower"})

    return response


@app.get("/cart/items")
def get_carts(request: Request, token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    cart = request.cookies.get(token)
    flowers = flowers_repository.get_flowers_list(flowers_id=cart, db=db)
    total = 0
    if flowers is None:
        raise HTTPException(status_code=404, detail= "cart is empty")
    for i in flowers:
        total += i.cost

    return {
        "flowers": flowers,
        "total": total,
    }


@app.post("/purchased")
def post_purchased(
        request: Request,
        flower_id: int = Form(),
        token: str = Depends(oauth2_schema),
        db: Session = Depends(get_db),
):
        user_id = decode(token)
        cart = request.cookies.get(token)
        cart_json = json.loads(cart)
        if flower_id not in cart_json:
            raise HTTPException(status_code=404, detail={"value": flower_id, "detail": "Flower doesn't have in basket"})
        purchase = PurchaseCreate(user_id=user_id, flower_id=flower_id)
        purchases_repository.add_purchase(db=db, purchase=purchase)
        return Response(status_code=200)


@app.get("/purchased")
def get_purchased(token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    user_id = decode(token)
    flowers_id_list = purchases_repository.get_by_user_id(user_id=user_id, db=db)
    flowers = flowers_repository.get_response_flowers(flowers_id=flowers_id_list, db=db)
    return flowers



