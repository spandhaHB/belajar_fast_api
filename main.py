from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
from database import engine, get_db, check_db_connection
from pydantic import BaseModel
from security import get_password_hash, verify_password

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Check database connection on startup
@app.on_event("startup")
async def startup_event():
    print("\nChecking database connection...")
    if not check_db_connection():
        print("Application will continue, but database operations may fail.")
    print("\nStarting FastAPI application...")

# Root endpoint with welcome message
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI"}

# Pydantic models for request/response
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

# Create user
@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Hash the password before storing
    hashed_password = get_password_hash(user.password)
    
    # Create user with hashed password
    db_user = models.User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Get all users
@app.get("/users/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# Get user by id
@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Update user
@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash the new password if it's provided
    if user.password:
        hashed_password = get_password_hash(user.password)
        db_user.password = hashed_password
    
    db_user.name = user.name
    db_user.email = user.email
    
    db.commit()
    db.refresh(db_user)
    return db_user

# Delete user
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}

# Verify password endpoint
@app.post("/users/verify-password/{user_id}")
def verify_user_password(user_id: int, password: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if verify_password(password, db_user.password):
        return {"message": "Password is correct"}
    else:
        raise HTTPException(status_code=401, detail="Incorrect password")