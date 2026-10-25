from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_guest: bool
    target_exam: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    target_exam: Optional[str] = "TNPSC Group 4"
    guest_user_id: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str
    guest_user_id: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    credential: str
    target_exam: Optional[str] = "TNPSC Group 4"
    guest_user_id: Optional[str] = None


class MergeGuestRequest(BaseModel):
    guest_user_id: Optional[str] = None
    guest_token: Optional[str] = None


class MergeResponse(BaseModel):
    merged: bool
    message: str
    bookmarks_merged: int = 0
    attempts_merged: int = 0
    revisions_merged: int = 0
    syllabus_merged: int = 0


class UpdateTargetExamRequest(BaseModel):
    target_exam: str
