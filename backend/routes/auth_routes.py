"""
Authentication Routes - User registration and login endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models.user_auth import UserAuth
from models.user_profiles import UserProfiles
from schemas.auth_schemas import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse
)
from security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Creates UserAuth with hashed password and associated UserProfiles.
    Returns access token and user data.
    
    Args:
        request: Registration data (full_name, email, password)
        db: Database session
        
    Returns:
        AuthResponse with access_token and user data
        
    Raises:
        HTTPException 409: Email already registered
        HTTPException 400: Invalid input data
    """
    # Check if email already exists
    existing_user = db.query(UserAuth).filter(UserAuth.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado"
        )
    
    try:
        # Create UserAuth with hashed password
        password_hashed = hash_password(request.password)
        user_auth = UserAuth(
            email=request.email,
            password_hash=password_hashed
        )
        db.add(user_auth)
        db.flush()  # Flush to get the generated ID
        
        # Create UserProfiles linked to UserAuth
        user_profile = UserProfiles(
            user_auth_id=user_auth.id,
            full_name=request.full_name
        )
        db.add(user_profile)
        db.commit()
        db.refresh(user_auth)
        db.refresh(user_profile)
        
        # Generate JWT token
        access_token = create_access_token(
            data={"sub": str(user_auth.id), "email": user_auth.email}
        )
        
        # Prepare response
        user_data = UserResponse(
            id=user_auth.id,
            email=user_auth.email,
            full_name=user_profile.full_name
        )
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_data
        )
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar usuário: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.
    
    Verifies credentials and returns JWT token with user data.
    
    Args:
        request: Login credentials (email, password)
        db: Database session
        
    Returns:
        AuthResponse with access_token and user data
        
    Raises:
        HTTPException 401: Invalid credentials
    """
    # Find user by email
    user_auth = db.query(UserAuth).filter(UserAuth.email == request.email).first()
    
    if not user_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos"
        )
    
    # Verify password
    if not verify_password(request.password, user_auth.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos"
        )
    
    # Get user profile
    user_profile = db.query(UserProfiles).filter(
        UserProfiles.user_auth_id == user_auth.id
    ).first()
    
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Perfil de usuário não encontrado"
        )
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(user_auth.id), "email": user_auth.email}
    )
    
    # Prepare response
    user_data = UserResponse(
        id=user_auth.id,
        email=user_auth.email,
        full_name=user_profile.full_name
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_data
    )
