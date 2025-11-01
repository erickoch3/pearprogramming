"""Pydantic models for authentication endpoints."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Request model for login endpoint."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Response model for login endpoint."""

    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    """Request model for creating a new user."""

    username: str
    password: str
