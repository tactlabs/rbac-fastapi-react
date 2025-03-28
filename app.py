from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import Dict
from passlib.context import CryptContext

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory database (for simplicity)
db_users: Dict[str, dict] = {
    "admin": {"username": "admin", "password": pwd_context.hash("admin123"), "role": "admin"}
}

# User Model
class User(BaseModel):
    username: str
    password: str
    role: str = "viewer"  # Default role is viewer

# Helper function
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    return db_users.get(username)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# User Registration
@app.post("/register")
async def register_user(username: str = Form(...), password: str = Form(...)):
    if username in db_users:
        raise HTTPException(status_code=400, detail="User already exists")
    db_users[username] = {"username": username, "password": pwd_context.hash(password), "role": "viewer"}
    return RedirectResponse(url="/", status_code=303)

# User Login
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = get_user(username)
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return RedirectResponse(url=f"/dashboard/{username}", status_code=303)

# Admin Dashboard
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request, "users": db_users})

# Update User Role (Only Admin)
@app.post("/admin/update-role")
async def update_role(username: str = Form(...), role: str = Form(...)):
    if username not in db_users:
        raise HTTPException(status_code=404, detail="User not found")
    db_users[username]["role"] = role
    return RedirectResponse(url="/admin", status_code=303)

# User Dashboard
@app.get("/dashboard/{username}", response_class=HTMLResponse)
async def user_dashboard(request: Request, username: str):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
