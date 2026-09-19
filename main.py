from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import models
from pydantic import BaseModel,Field
from models import Users, Couriers, PasswordResetOtp
from database import SessionLocal, engine
from fastapi.responses import JSONResponse
from router import admin, auth,rider
from router.auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


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
    couriers = db.query(Couriers).filter(Couriers.customer_id == user.get('id')).all()
    if not couriers:
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

@app.get('/user')
def get_user_details(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    current_user = db.query(Users).filter(Users.id == user.get('id')).first()
    if current_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    return {
        'id': current_user.id,
        'email': current_user.email,
        'username': current_user.username,
        'firstname': current_user.firstname,
        'lastname': current_user.lastname,
        'role': current_user.role,
        'is_active': current_user.is_active,
        'created_at': current_user.created_at
    }

@app.get('/courier/view/{courier_id}')
def view_specific_courier(user: user_dependency, db: db_dependency, courier_id:int):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    courier = db.query(Couriers).filter(Couriers.customer_id == user.get('id')).filter(Couriers.id == courier_id).first()
    if courier is None:
        raise HTTPException(status_code=404, detail='Courier not found')
    return {
        'id': courier.id,
        'customer_id': courier.customer_id,
        'sending_from': courier.sending_from,
        'destination': courier.destination,
        'receiver_name': courier.receiver_name,
        'weight': courier.weight,
        'bill': courier.bill,
        'is_aproved': courier.is_aproved,
        'assigned_rider': courier.assigned_rider,
        'is_completed': courier.is_completed
        }


@app.delete('courier/cancel/{courier_id}')
def cancel_courier(user: user_dependency, db: db_dependency, courier_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    courier = db.query(Couriers).filter(Couriers.id == courier_id).first()
    if courier.is_aproved != False:
        raise JSONResponse(status_code=403, content={'message':'Already Aproved, Cannot Cancel Now'})
    db.query(Couriers).filter(Couriers.id == courier_id).delete()

    db.commit()
    return JSONResponse(status_code=200, content={'message':'Courier deleted Successfully'})
