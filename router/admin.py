from fastapi import FastAPI, APIRouter,Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel,Field
from models import Users
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from typing import Annotated, Optional
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt,JWTError
from router.auth import get_current_user

router = APIRouter()