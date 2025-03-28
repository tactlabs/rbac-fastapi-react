from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app location
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token settings
SECRET_KEY = "your-secret-key"  # In production, use a secure random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# User database (in-memory for demonstration)
users_db = {}

# Debug endpoints
@app.get("/debug/users")
async def debug_get_users():
    return {"users": users_db}

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    result = pwd_context.verify(plain_password, hashed_password)
    print(f"Verifying password: {plain_password} against hash: {hashed_password}, result: {result}")
    return result

def get_user(username: str) -> Optional[Dict]:
    user = users_db.get(username)
    print(f"Getting user {username}, found: {user is not None}")
    return user

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    print(f"Authentication attempt for user: {username}")
    print(f"Current users in DB: {list(users_db.keys())}")
    user = get_user(username)
    if not user:
        print(f"User {username} not found")
        return None
    if not verify_password(password, user["hashed_password"]):
        print(f"Password verification failed for user {username}")
        return None
    print(f"Authentication successful for user {username}")
    return user

# ... rest of your app code 