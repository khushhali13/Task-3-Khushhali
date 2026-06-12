from sqlalchemy.orm import Session
import models
import schemas
import auth

def get_user(db: Session, user_id: int):
    """Retrieve a user by their ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    """Retrieve a user by their username (useful for duplicate prevention)."""
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    """Retrieve a user by their email (useful for duplicate prevention)."""
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Retrieve a list of users with pagination."""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user with a securely hashed password."""
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=auth.get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    """Update user fields. Only updates fields that are explicitly provided."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
        
    update_data = user_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        if key == "password":
            db_user.hashed_password = auth.get_password_hash(value)
        else:
            setattr(db_user, key, value)
            
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    """Delete a user by ID."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    db.delete(db_user)
    db.commit()
    return db_user
