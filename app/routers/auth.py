from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import (
    SignupRequest,
    SigninRequest,
    TokenResponse
)
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)


# ==============================
# ROUTER
# ==============================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ==============================
# SIGNUP
# ==============================

@router.post("/signup")
def signup(
    user_data: SignupRequest,
    db: Session = Depends(get_db)
):
    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(
        user_data.password
    )

    # Create user
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": str(new_user.id),
        "email": new_user.email
    }


# ==============================
# SIGNIN
# ==============================

@router.post(
    "/signin",
    response_model=TokenResponse
)
def signin(
    user_data: SigninRequest,
    db: Session = Depends(get_db)
):
    # Find user by email
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    # Check email
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Check password
    if not verify_password(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create JWT token
    access_token = create_access_token({
        "sub": str(user.id)
    })

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ==============================
# PROTECTED HOME
# ==============================

@router.get("/home")
def home(
    user_id: str = Depends(get_current_user)
):
    return {
        "message": "Welcome to the Home Page",
        "user_id": user_id
    }