from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import json
import os

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

# User database with file persistence
USERS_FILE = "users_db.json"

# Initialize empty users_db
users_db = {}

# Load existing users if file exists
if os.path.exists(USERS_FILE):
    try:
        with open(USERS_FILE, "r") as f:
            users_db = json.load(f)
    except json.JSONDecodeError:
        # If the file is corrupted, start with empty database
        users_db = {}

# Function to save users to file
def save_users_to_file():
    with open(USERS_FILE, "w") as f:
        json.dump(users_db, f)

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
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str) -> Optional[Dict]:
    if username in users_db:
        return users_db[username]
    return None

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return user

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
    # Save to file
    save_users_to_file()
    
    # Return user data (excluding password)
    return UserResponse(
        username=user.username,
        email=user.email,
        full_name=user.full_name
    )

@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"]
    )
