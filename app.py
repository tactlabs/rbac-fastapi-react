from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from passlib.context import CryptContext

app = FastAPI()

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User database (in-memory for demonstration)
users_db = {}

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

@app.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    # Check if username already exists
    if user.username in users_db:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Hash the password
    hashed_password = pwd_context.hash(user.password)
    
    # Create user dict (excluding password from response)
    user_data = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_password
    }
    
    # Store user in database
    users_db[user.username] = user_data
    
    # Return user data (excluding password)
    return UserResponse(
        username=user.username,
        email=user.email,
        full_name=user.full_name
    )
