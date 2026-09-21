from fastapi import FastAPI, APIRouter,Depends, HTTPException
from sqlalchemy.orm import Session
from models import Couriers
from fastapi.responses import JSONResponse
from typing import Annotated
from database import SessionLocal
from router.auth import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.put('/rider/complete/{order_id}')
def complete_courier(user: user_dependency,db: db_dependency,order_id: int):
    if user is None or user.get('role') != "rider":
        raise HTTPException(status_code=403,detail="Failed Authentication")

    courier = db.query(Couriers).filter(Couriers.id == order_id).first()

    if courier is None:
        raise HTTPException(status_code=404,detail="Courier not found")


    if courier.assigned_rider != user.get("id"):
        raise HTTPException(status_code=403,detail="This courier is not assigned to you")

    if courier.is_completed:
        raise HTTPException(status_code=400,detail="Courier is already completed")

    courier.is_completed = True
    courier.status = "completed"

    db.commit()

    return JSONResponse(status_code=200,content={"message": "Courier completed successfully"})

@router.get('/rider/all_orders')
def view_all_order(
    user: user_dependency,
    db: db_dependency
):
    if user is None or user.get('role') != "rider":
        raise HTTPException(status_code=403,detail="Failed Authentication")

    orders = db.query(Couriers).filter(Couriers.assigned_rider == user.get("id")).all()

    return [
        {
            "id": order.id,
            "customer_id": order.customer_id,
            "sending_from": order.sending_from,
            "destination": order.destination,
            "receiver_name": order.receiver_name,
            "weight": order.weight,
            "bill": order.bill,
            "is_aproved": order.is_aproved,
            "assigned_rider": order.assigned_rider,
            "is_completed": order.is_completed,
            "status": order.status
        }
        for order in orders
    ]