from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import json
import os
from enum import Enum

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
        print(f"Loaded {len(users_db)} users from {USERS_FILE}")
    except json.JSONDecodeError:
        # If the file is corrupted, start with empty database
        users_db = {}
        print(f"Error loading users from {USERS_FILE}, starting with empty database")
else:
    print(f"No users file found at {USERS_FILE}, starting with empty database")

# Function to save users to file
def save_users_to_file():
    with open(USERS_FILE, "w") as f:
        json.dump(users_db, f)
    print(f"Saved {len(users_db)} users to {USERS_FILE}")

# Add Role enum
class Role(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"

# Modify UserCreate model
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Role = Role.VIEWER  # Default role is viewer

# Modify UserResponse model
class UserResponse(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: Role

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    print(f"Verifying password for hashed: {hashed_password[:10]}...")
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str) -> Optional[Dict]:
    if username in users_db:
        print(f"User found: {username}")
        return users_db[username]
    print(f"User not found: {username}")
    return None

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    print(f"Authentication attempt for: {username}")
    print(f"Available users: {list(users_db.keys())}")
    user = get_user(username)
    if not user:
        print(f"No user record found for {username}")
        return None
    if not verify_password(password, user["hashed_password"]):
        print(f"Password verification failed for {username}")
        return None
    print(f"Authentication successful for {username}")
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

# Debug endpoint to check what users are in the database
@app.get("/debug/users")
async def debug_get_users():
    return {"user_count": len(users_db), "usernames": list(users_db.keys())}

# Debug endpoint to check a specific user
@app.get("/debug/user/{username}")
async def debug_get_user(username: str):
    user = get_user(username)
    if not user:
        return {"exists": False}
    # Return user info but don't expose the full hashed password
    safe_user = {**user}
    if "hashed_password" in safe_user:
        password_preview = safe_user["hashed_password"][:10] + "..." if safe_user["hashed_password"] else None
        safe_user["hashed_password_preview"] = password_preview
        del safe_user["hashed_password"]
    return {"exists": True, "user": safe_user}

# Add role verification dependency
async def verify_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action"
        )
    return current_user

# Modify register_user function to include role
@app.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    print(f"Registration attempt for: {user.username}")
    # Check if username already exists
    if user.username in users_db:
        print(f"Username already exists: {user.username}")
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Hash the password
    hashed_password = pwd_context.hash(user.password)
    print(f"Password hashed for {user.username}: {hashed_password[:10]}...")
    
    user_data = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_password,
        "role": Role.VIEWER  # New users always start as viewers
    }
    
    # Store user in database
    users_db[user.username] = user_data
    print(f"Added user to database: {user.username}")
    # Save to file
    save_users_to_file()
    
    return UserResponse(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user_data["role"]
    )

@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"Login attempt for: {form_data.username}")
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        print(f"Authentication failed for: {form_data.username}")
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
    print(f"Generated token for: {form_data.username}")
    
    return {"access_token": access_token, "token_type": "bearer"}

# Add new endpoint for updating user roles
class UpdateUserRole(BaseModel):
    username: str
    new_role: Role

@app.put("/users/{username}/role", response_model=UserResponse)
async def update_user_role(
    username: str,
    role_update: UpdateUserRole,
    admin: dict = Depends(verify_admin)
):
    if username not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    users_db[username]["role"] = role_update.new_role
    save_users_to_file()
    
    return UserResponse(
        username=users_db[username]["username"],
        email=users_db[username]["email"],
        full_name=users_db[username]["full_name"],
        role=users_db[username]["role"]
    )

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"]
    )
