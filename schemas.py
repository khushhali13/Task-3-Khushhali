from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# Standard email validation regex pattern to avoid external email-validator package dependency
EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
USERNAME_PATTERN = r"^[a-zA-Z0-9_-]+$"

class UserBase(BaseModel):
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        pattern=USERNAME_PATTERN, 
        description="Alphanumeric characters, underscores, and hyphens only."
    )
    email: str = Field(
        ..., 
        pattern=EMAIL_PATTERN, 
        description="Must be a valid email format."
    )
    full_name: Optional[str] = Field(None, max_length=100, description="Full name of the user.")

class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=6, 
        description="Password must be at least 6 characters long."
    )

class UserUpdate(BaseModel):
    username: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=50, 
        pattern=USERNAME_PATTERN
    )
    email: Optional[str] = Field(None, pattern=EMAIL_PATTERN)
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        # Pydantic v2 compatible configuration to read database models
        from_attributes = True

# --- Authentication Schemas ---

class Token(BaseModel):
    """Schema for the JWT token response returned during login."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for the data payload inside the JWT."""
    username: Optional[str] = None
