"""
Authentication Schemas - Request/Response validation for auth endpoints
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID
from typing import Optional


class RegisterRequest(BaseModel):
    """Request schema for user registration"""
    full_name: str = Field(..., min_length=3, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Validate and clean full name"""
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Nome deve ter pelo menos 3 caracteres')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres')
        return v


class LoginRequest(BaseModel):
    """Request schema for user login"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")


class UserResponse(BaseModel):
    """Response schema for user data (without sensitive info)"""
    id: UUID = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    
    class Config:
        from_attributes = True  # Allows creating from ORM models


class AuthResponse(BaseModel):
    """Response schema for authentication (login/register)"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")
