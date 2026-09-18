from fastapi import FastAPI, APIRouter,Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel
from models import Users
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from typing import Annotated,Literal
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt,JWTError

router = APIRouter()

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY = '6a1c71aa7ffc910afb747733a5be5ec7ecba014ee944ec281d956b7103f58a26'
AGORITHM = 'HS256'


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
    return jwt.encode(encode, SECRET_KEY, algorithm=AGORITHM)

def get_current_user(token: Annotated[str, Depends(OAuth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[AGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=404, detail='User not Found')
        return{'username': username,'id': user_id, 'role': role}
    except:
        raise HTTPException(status_code=404, detail='User not Found')

class CreateUsers(BaseModel):
    email: str
    username: str
    firstname: str
    lastname: str
    password: str
    role: Literal["admin", "customer", "rider"]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

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

    return JSONResponse(status_code=201, content={'message': 'User added Successfully'})


@router.post('/login')
def login_user(db : db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):

    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        return "Faild authentication"

    token = create_access_token(user.username, user.id, user.role,timedelta(minutes=30))
    return {'access_token': token, 'token_type': 'bearer'}