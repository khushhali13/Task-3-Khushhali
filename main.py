from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

# Import local database and CRUD modules
from database import SessionLocal, engine, Base
import crud
import schemas
import models
import auth

# Automatically create database tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="User Directory API",
    description="FastAPI CRUD backend with SQLite database integration",
)

# Set up CORS middleware to allow testing from different origins if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# to yield database session and close it after the request lifecycle
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# for api endpoints:

# --- Authentication Endpoints ---

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint. Users send their username and password here.
    If correct, they receive a JWT token to use for protected routes.
    """
    # 1. Find user by username
    user = crud.get_user_by_username(db, username=form_data.username)
    
    # 2. Check if user exists and password is correct
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Create the JWT token
    access_token = auth.create_access_token(data={"sub": user.username})
    
    # 4. Return the token
    return {"access_token": access_token, "token_type": "bearer"}

# --- Protected Endpoints Example ---

@app.get("/api/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """
    A protected route! Notice how it uses 'Depends(auth.get_current_user)'.
    This forces the user to send a valid JWT token. 
    It returns the profile of the currently logged-in user.
    """
    return current_user

# --- Standard CRUD Endpoints ---

@app.get("/")
def read_root():
    return {
        "status": "Online",
        "message": "User Directory CRUD API is running successfully.",
        "documentation": "/docs"
    }


@app.post("/api/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    Validates duplicate entries by checking if the username or email is already registered.
    """
    # Prevent duplicate username
    db_username = crud.get_user_by_username(db, username=user.username)
    if db_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered."
        )
        
    # Prevent duplicate email
    db_email = crud.get_user_by_email(db, email=user.email)
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )
        
    return crud.create_user(db=db, user=user)


@app.get("/api/users/", response_model=List[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve all user records with optional pagination (skip and limit)."""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/api/users/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific user record by its ID. Raises 404 if not found."""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found."
        )
    return db_user


@app.put("/api/users/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    """
    Update a specific user record by its ID.
    Handles duplicate prevention if username or email is being updated.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found."
        )
        
    # Prevent duplicate username if username is changing
    if user_update.username and user_update.username != db_user.username:
        duplicate = crud.get_user_by_username(db, username=user_update.username)
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken by another user."
            )
            
    # Prevent duplicate email if email is changing
    if user_update.email and user_update.email != db_user.email:
        duplicate = crud.get_user_by_email(db, email=user_update.email)
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already taken by another user."
            )
            
    updated_user = crud.update_user(db=db, user_id=user_id, user_update=user_update)
    return updated_user


@app.delete("/api/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user record by its ID. Raises 404 if not found."""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found."
        )
    crud.delete_user(db=db, user_id=user_id)
    return {"message": f"User with ID {user_id} has been deleted successfully."}
