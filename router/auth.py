from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel, Field
from models import Users, PasswordResetOtp
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from typing import Annotated, Literal, Optional
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt

import random
import smtplib
from email.message import EmailMessage

router = APIRouter()

bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

OAuth2_bearer = OAuth2PasswordBearer(tokenUrl="login")


SECRET_KEY = "YOUR_SECRET_KEY_HERE"
ALGORITHM = "HS256"

EMAIL_ADDRESS = "arfinaleusuf@gmail.com"
EMAIL_PASSWORD = "ujxjimlgbtvdjexi"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


class CreateUsers(BaseModel):
    email: str
    username: str
    firstname: str
    lastname: str
    password: str
    role: Literal["admin", "customer", "rider"]


class UpdateUser(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None


class UpdatePassword(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def authenticate_user(username, password, db):
        user = db.query(Users).filter(Users.username == username).first()
        if user is None:
            return False
        
        if bcrypt_context.verify(password, user.hash_password):
            return user
        else:
            return False

def create_access_token(username: str, user_id: int, role: str, expires_delta : timedelta):
    encode = {'sub':username, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: Annotated[str, Depends(OAuth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=404, detail='User not Found')
        return{'username': username,'id': user_id, 'role': role}
    except:
        raise HTTPException(status_code=404, detail='User not Found')

@router.post('/createuser')
def createuser(db: db_dependency, new_user: CreateUsers):
    user_model = Users(
        email = new_user.email,
        username = new_user.username,
        firstname = new_user.firstname,
        lastname = new_user.lastname,
        hash_password = bcrypt_context.hash(new_user.password),
        is_active = True,
        role = new_user.role
    )
    db.add(user_model)
    db.commit()

    return JSONResponse(status_code=201, content={'messege': 'User added Successfully'})

@router.post("/login")
def login_user(db: db_dependency,form_data: Annotated[OAuth2PasswordRequestForm,Depends()]):

    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=401,detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=403,detail="User account is inactive")
    token = create_access_token(user.username,user.id,user.role,timedelta(minutes=30))
    return {"access_token": token,"token_type": "bearer"}

user_dependency = Annotated[dict,Depends(get_current_user)]

@router.put("/passwordChange")
def update_password(user: user_dependency,db: db_dependency,update_password: UpdatePassword):
    current_user = db.query(Users).filter(Users.id == user.get("id")).first()

    if current_user is None:
        raise HTTPException(status_code=401,detail="User not found")

    if not bcrypt_context.verify(update_password.current_password,current_user.hash_password):
        raise HTTPException(status_code=401,detail="Wrong password")

    current_user.hash_password = bcrypt_context.hash(update_password.new_password)

    db.commit()

    return {"message": "Password updated successfully"}

@router.put("/edituser")
def update_user(user: user_dependency,db: db_dependency,update_user: UpdateUser):

    current_user = db.query(Users).filter(Users.id == user.get("id")).first()

    if current_user is None:
        raise HTTPException(status_code=401,detail="User not found")
    
    update_data = update_user.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(current_user,key,value)

    db.commit()
    return {
        "message": "User updated successfully"
    }


def send_otp_email(receiver_email: str,otp: str):
    msg = EmailMessage()
    msg["Subject"] = "Courier App - Password Reset OTP"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = receiver_email
    msg.set_content(
        f"""
Hello,

Your Courier App password reset OTP is:

{otp}

This OTP will expire in 5 minutes.

If you did not request a password reset,
please ignore this email.

Thank you.
Bangladesh Courier Service.
"""
    )

    try:
        with smtplib.SMTP(SMTP_SERVER,SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_ADDRESS,EMAIL_PASSWORD)
            server.send_message(msg)

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=500,detail="Gmail authentication failed. Check your App Password.")

    except Exception as e:
        print("Email error:", e)
        raise HTTPException(status_code=500,detail="Failed to send OTP email")

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest,db: db_dependency):

    user = db.query(Users).filter(Users.email == request.email).first()

    if user is None:
        raise HTTPException(status_code=404,detail="User not found")

    otp = str(random.randint(100000,999999))

    reset_otp = PasswordResetOtp(
        user_id = user.id,
        otp = bcrypt_context.hash(otp),
        expires_at = datetime.now() + timedelta(minutes=5),
        is_used = False
    )

    send_otp_email(user.email,otp)

    db.add(reset_otp)

    db.commit()

    return {"message": "OTP sent successfully"}

@router.post("/verify-otp")
def verify_otp(request: VerifyOtpRequest,db: db_dependency):
    user = db.query(Users).filter(Users.email == request.email).first()

    if user is None:
        raise HTTPException(status_code=404,detail="User not found")

    reset_data = (
        db.query(PasswordResetOtp)
        .filter(PasswordResetOtp.user_id == user.id,PasswordResetOtp.is_used == False)
        .order_by(PasswordResetOtp.id.desc()).first()
    )

    if reset_data is None:
        raise HTTPException(status_code=400,detail="OTP not found")

    if reset_data.expires_at < datetime.now():
        raise HTTPException(status_code=400,detail="OTP expired")
    
    if not bcrypt_context.verify(request.otp,reset_data.otp):
        raise HTTPException(status_code=400,detail="Invalid OTP")
    
    return {
        "message": "OTP verified successfully"
    }

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest,db: db_dependency):
    user = db.query(Users).filter(Users.email == request.email).first()

    if user is None:
        raise HTTPException(status_code=404,detail="User not found")

    reset_data = (
        db.query(PasswordResetOtp)
        .filter(PasswordResetOtp.user_id == user.id,PasswordResetOtp.is_used == False)
        .order_by(PasswordResetOtp.id.desc()).first())

    if reset_data is None:
        raise HTTPException(status_code=400,detail="OTP not found")

    if reset_data.expires_at < datetime.now():
        raise HTTPException(status_code=400,detail="OTP expired")
    
    if not bcrypt_context.verify(request.otp,reset_data.otp):
        raise HTTPException(status_code= 400,detail="Invalid OTP")
    
    user.hash_password = bcrypt_context.hash(request.new_password)
    reset_data.is_used = True

    db.commit()

    return {
        "message": "Password reset successfully"
    }