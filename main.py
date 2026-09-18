from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import models
from pydantic import BaseModel,Field
from models import Users, Couriers, PasswordResetOtp
from database import SessionLocal, engine
from fastapi.responses import JSONResponse
from router import admin, auth
from router.auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(admin.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class CouriersCreate(BaseModel):
    sending_from: str
    destination: str
    receiver_name: str
    weight: float

@app.get('/my/couriers')
def get_my_all_couriers(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    couriers = db.query(Couriers).filter(Couriers.customer_id == user.id).all()
    if couriers is None:
        raise HTTPException(status_code=404, detail='No Couriers found')
    return couriers

@app.post('/create_courier')
def create_new_courier(user: user_dependency, db: db_dependency, new_courier : CouriersCreate):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    cost_per_kg = 100
    total_cost = new_courier.weight * cost_per_kg
    courier_model = Couriers(
        **new_courier.model_dump(),
        customer_id = user.get("id"),
        bill = total_cost
    )
    db.add(courier_model)
    db.commit()
    return JSONResponse(status_code=201, content={'message':'Courier Added Successfully'})