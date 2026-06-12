from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import models
from database import SessionLocal

# --- Security Configuration ---
# In a real production application, this SECRET_KEY MUST be read from an environment variable!
# For this internship project, we are hardcoding it for simplicity.
SECRET_KEY = "your-super-secret-key-for-internship-project"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Passlib context for hashing passwords using the modern bcrypt algorithm.
# bcrypt automatically adds a unique "salt" to each password, making it extremely secure.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer tells FastAPI where to look for the token.
# It expects the token in the request header: 'Authorization: Bearer <token>'
# The 'tokenUrl' is the endpoint where users will send their username and password to get a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Password Utilities ---

def verify_password(plain_password, hashed_password):
    """
    Checks if the provided plain text password matches the hashed password from the database.
    This is used during the login process.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Hashes a plain text password before saving it to the database.
    This ensures that if the database is ever leaked, the passwords remain unreadable.
    """
    return pwd_context.hash(password)

# --- JWT Utilities ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Generates a new JSON Web Token (JWT).
    The JWT contains a 'payload' (the data like username), an expiration time, 
    and is securely signed with our SECRET_KEY so users can't tamper with it.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default expiration time is 15 minutes if not specified
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    
    # Create the token using the secret key and the chosen algorithm (HS256)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependency for Protected Routes ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    This is a 'Dependency' in FastAPI.
    It automatically runs when a user tries to access a protected route.
    1. It takes the token from the incoming request.
    2. It decodes the token to find out who the user is (their username).
    3. It fetches the user from the database and returns it.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token using our secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        # If the token is invalid, tampered with, or expired, we throw a 401 Unauthorized error
        raise credentials_exception
        
    # Find the user in the database
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
