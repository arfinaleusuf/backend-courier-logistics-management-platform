from fastapi import Query, APIRouter,Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from models import Users, Couriers
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

@router.get('/admin/all_courier/{page}')
def view_all_courier(page: int,user: user_dependency,db: db_dependency,
    sort_by: str = Query(
        default='newest',
        description='Select newest or oldest'
    ),
    order: str = Query(
        default='desc',
        description='Select asc or desc for bill'
    )
):

    if user is None or user.get('role') != "admin":
        raise HTTPException(status_code=403,detail="Failed Authentication")

    if page < 1:
        raise HTTPException(status_code=400,detail="Page must be greater than 0")

    if sort_by not in ["newest", "oldest"]:
        raise HTTPException(status_code=400,detail="sort_by must be newest or oldest")

    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400,detail="order must be asc or desc")

    limit = 10

    query = db.query(Couriers).filter(
        Couriers.is_completed == False
    )

    if sort_by == "newest":
        query = query.order_by(Couriers.id.desc())

    else:
        query = query.order_by(Couriers.id.asc())


    total_couriers = query.count()

    skip = (page - 1) * limit

    couriers = (query.offset(skip).limit(limit).all())

    total_pages = (total_couriers + limit - 1) // limit

    return {
        "page": page,
        "per_page": limit,
        "total_couriers": total_couriers,
        "total_pages": total_pages,
        "sort_by": sort_by,
        "order": order,
        "couriers": couriers
    }

@router.get('/admin/all_request')
def view_all_request(user:user_dependency, db: db_dependency):
    if user is None or user.get('role') != "admin":
        raise HTTPException(status_code=403, detail="Failed Authentication")
    couriers = db.query(Couriers).filter(Couriers.is_aproved == False).all()  
    return couriers

@router.get('/admin/all_rider')
def view_all_rider(user:user_dependency, db: db_dependency):
    if user is None or user.get('role') != "admin":
        raise HTTPException(status_code=403, detail="Failed Authentication")
    riders = db.query(Users).filter(Users.role == "rider").all()  
    return [
        {
            "id": rider.id,
            "username": rider.username,
            "email": rider.email,
            "firstname": rider.firstname,
            "lastname": rider.lastname,
            "role": rider.role,
            "created_at": rider.created_at,
            "is_active": rider.is_active
        }
        for rider in riders
    ]

from datetime import date, datetime, time
from fastapi import Query


@router.get('/admin/filter_courier')
def filter_courier(
    user: user_dependency,
    db: db_dependency,
    status: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None)
):

    if user is None or user.get('role') != "admin":
        raise HTTPException(
            status_code=403,
            detail="Failed Authentication"
        )

    # Valid status
    valid_status = [
        "pending",
        "approved",
        "assigned",
        "completed"
    ]

    if status is not None and status not in valid_status:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Select from {valid_status}"
        )

    # Date validation
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be greater than to_date"
        )

    query = db.query(Couriers)

    # Status filter
    if status:
        query = query.filter(
            Couriers.status == status
        )

    # From date
    if from_date:
        query = query.filter(
            Couriers.created_at >= datetime.combine(
                from_date,
                time.min
            )
        )

    # To date
    if to_date:
        query = query.filter(
            Couriers.created_at <= datetime.combine(
                to_date,
                time.max
            )
        )

    couriers = query.all()

    return {
        "total": len(couriers),
        "couriers": couriers
    }

@router.get('/admin/all_customer')
def view_all_customer(user:user_dependency, db: db_dependency):
    if user is None or user.get('role') != "admin":
        raise HTTPException(status_code=403, detail="Failed Authentication")
    customers = db.query(Users).filter(Users.role == "customer").all()  
    return [
        {
            "id": customer.id,
            "username": customer.username,
            "email": customer.email,
            "firstname": customer.firstname,
            "lastname": customer.lastname,
            "role": customer.role,
            "created_at": customer.created_at,
            "is_active": customer.is_active
        }
        for customer in customers
    ]

@router.get('/admin/search_customer/{name}')
def search_customer(
    user: user_dependency,
    db: db_dependency,
    name: str
):
    if user is None or user.get('role') != "admin":
        raise HTTPException(
            status_code=403,
            detail="Failed Authentication"
        )

    customers = db.query(Users).filter(
        Users.role == "customer",(Users.firstname.ilike(f"%{name}%")) | (Users.lastname.ilike(f"%{name}%"))).all()

    return [
        {
            "id": customer.id,
            "username": customer.username,
            "email": customer.email,
            "firstname": customer.firstname,
            "lastname": customer.lastname,
            "role": customer.role,
            "created_at": customer.created_at,
            "is_active": customer.is_active
        }
        for customer in customers
    ]

@router.get('/admin/search_rider/{name}')
def search_rider(
    user: user_dependency,
    db: db_dependency,
    name: str
):
    if user is None or user.get('role') != "admin":
        raise HTTPException(
            status_code=403,
            detail="Failed Authentication"
        )

    riders = db.query(Users).filter(Users.role == "rider",(Users.firstname.ilike(f"%{name}%")) |(Users.lastname.ilike(f"%{name}%"))).all()

    return [
        {
            "id": rider.id,
            "username": rider.username,
            "email": rider.email,
            "firstname": rider.firstname,
            "lastname": rider.lastname,
            "role": rider.role,
            "created_at": rider.created_at,
            "is_active": rider.is_active
        }
        for rider in riders
    ]

@router.put('/admin/approve/{order_id}')
def approve_request(user:user_dependency, db: db_dependency, order_id: int):
    if user is None or user.get('role') != "admin":
        raise HTTPException(status_code=403, detail="Failed Authentication")
    courier = db.query(Couriers).filter(Couriers.id == order_id).first()  
    if courier is None:
        raise HTTPException(status_code=404, detail='Courier not found')
    if courier.is_aproved:
        raise HTTPException(status_code=400,detail="Courier already approved")

    courier.is_aproved = True
    courier.status = "approved"
    db.commit()
    return JSONResponse(status_code=200, content={'message' : 'Courier Approved successfully'})

@router.put('/admin/assign_rider/{order_id}/{rider_id}')
def assign_rider(user:user_dependency, db: db_dependency, order_id: int, rider_id:int):
    if user is None or user.get('role') != "admin":
        raise HTTPException(status_code=403, detail="Failed Authentication")
    courier = db.query(Couriers).filter(Couriers.id == order_id).first()  
    if courier is None:
        raise HTTPException(status_code=404, detail='Courier not found')

    if not courier.is_aproved:
        raise HTTPException(status_code=400,detail="Courier is not approved yet")

    rider = db.query(Users).filter(Users.id == rider_id,Users.role == "rider").first()
    if rider is None:
        raise HTTPException(
            status_code=404,
            detail="Rider not found"
        )

    courier.assigned_rider = rider_id
    courier.status = "assigned"

    db.commit()
    return JSONResponse(status_code=200, content={'message' : 'Rider assigned successfully'})
