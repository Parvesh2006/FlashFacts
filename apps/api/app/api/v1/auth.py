import json
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    base64url_decode,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user,
    get_current_user_optional,
)
from app.models.user import User
from app.models.pyq_bookmark import PYQBookmark
from app.models.mock_test import MockTestAttempt
from app.models.revision_item import RevisionItem
from app.models.syllabus import UserSyllabusProgress
from app.schemas.auth import (
    UserResponse,
    TokenResponse,
    RegisterRequest,
    LoginRequest,
    GoogleAuthRequest,
    MergeGuestRequest,
    MergeResponse,
    UpdateTargetExamRequest,
)

router = APIRouter()


def merge_guest_data(db: Session, guest_id: str, target_user: User) -> Dict[str, int]:
    """
    Safely merges guest bookmarks, mock test attempts, revision mistakes,
    and syllabus progress into target_user profile without duplicate key violations.
    """
    if not guest_id or guest_id == target_user.id:
        return {"bookmarks": 0, "attempts": 0, "revisions": 0, "syllabus": 0}

    counts = {"bookmarks": 0, "attempts": 0, "revisions": 0, "syllabus": 0}

    # 1. Merge PYQ Bookmarks
    guest_bookmarks = db.query(PYQBookmark).filter(PYQBookmark.user_id == guest_id).all()
    for bm in guest_bookmarks:
        existing = db.query(PYQBookmark).filter(
            PYQBookmark.user_id == target_user.id,
            PYQBookmark.pyq_id == bm.pyq_id,
        ).first()
        if not existing:
            bm.user_id = target_user.id
            counts["bookmarks"] += 1
        else:
            db.delete(bm)

    # 2. Merge Mock Test Attempts
    guest_attempts = db.query(MockTestAttempt).filter(MockTestAttempt.user_id == guest_id).all()
    for att in guest_attempts:
        att.user_id = target_user.id
        counts["attempts"] += 1

    # 3. Merge Revision Items (Mistake Book)
    guest_revisions = db.query(RevisionItem).filter(RevisionItem.user_id == guest_id).all()
    for rev in guest_revisions:
        existing_rev = db.query(RevisionItem).filter(
            RevisionItem.user_id == target_user.id,
            RevisionItem.question_text == rev.question_text,
        ).first()
        if not existing_rev:
            rev.user_id = target_user.id
            counts["revisions"] += 1
        else:
            # Keep highest mistake count and latest review
            existing_rev.mistake_count = max(existing_rev.mistake_count, rev.mistake_count)
            db.delete(rev)

    # 4. Merge Syllabus Progress
    guest_prog = db.query(UserSyllabusProgress).filter(UserSyllabusProgress.user_id == guest_id).all()
    for sp in guest_prog:
        existing_sp = db.query(UserSyllabusProgress).filter(
            UserSyllabusProgress.user_id == target_user.id,
            UserSyllabusProgress.topic_id == sp.topic_id,
        ).first()
        if not existing_sp:
            sp.user_id = target_user.id
            counts["syllabus"] += 1
        else:
            if sp.status == "completed":
                existing_sp.status = "completed"
            db.delete(sp)

    # Clean up guest user record if it was an auto-generated guest
    guest_user = db.query(User).filter(User.id == guest_id).first()
    if guest_user and guest_user.is_guest:
        db.delete(guest_user)

    db.commit()
    return counts


def verify_google_credential(credential: str) -> Dict[str, Any]:
    """Verify a Google ID token through Google's tokeninfo endpoint."""
    if not credential or not credential.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google credential token is required",
        )

    client_id = settings.GOOGLE_CLIENT_ID.strip()
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured on the server",
        )

    import httpx

    try:
        response = httpx.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": credential},
            timeout=8.0,
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google verification service is temporarily unavailable",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google credential",
        )

    try:
        data = response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google verification response",
        )

    if data.get("aud") != client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token client ID mismatch",
        )

    email = data.get("email")
    subject = data.get("sub")

    if (
        not isinstance(email, str)
        or not email.strip()
        or data.get("email_verified") not in (True, "true")
        or not isinstance(subject, str)
        or not subject.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is not verified or required claims are missing",
        )

    return {
        "email": email.strip().lower(),
        "name": data.get("name") or email.split("@")[0],
        "sub": subject,
    }


@router.post("/guest", response_model=TokenResponse)
def guest_session(target_exam: str = "TNPSC Group 4", db: Session = Depends(get_db)):
    """Create or retrieve a guest session token for immediate frictionless exam portal access."""
    user = User.create_guest(target_exam=target_exam)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "username": user.username})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new student account with username and password, with optional guest data merge."""
    existing_user = db.query(User).filter(User.username == req.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    if req.email:
        existing_email = db.query(User).filter(User.email == req.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        is_guest=False,
        target_exam=req.target_exam or "TNPSC Group 4",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Merge guest data if previous guest session ID was provided
    if req.guest_user_id:
        try:
            merge_guest_data(db, req.guest_user_id, user)
        except Exception:
            pass

    token = create_access_token({"sub": user.id, "username": user.username})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Log in with existing student credentials, with optional guest data merge."""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Merge guest data if previous guest session ID was provided
    if req.guest_user_id:
        try:
            merge_guest_data(db, req.guest_user_id, user)
        except Exception:
            pass

    token = create_access_token({"sub": user.id, "username": user.username})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/google", response_model=TokenResponse)
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate or register via Google Sign-In (ID token).
    Seamlessly merges existing guest session data into the student account.
    """
    info = verify_google_credential(req.credential)
    email = info["email"]
    name = info.get("name") or email.split("@")[0]

    # Look up existing user by email
    user = db.query(User).filter(User.email == email).first()

    if user:
        if user.is_guest:
            user.is_guest = False
            user.updated_at = datetime.now(timezone.utc)
            db.commit()
    else:
        # Create unique username
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "", name.lower().replace(" ", "_"))[:25]
        base_username = clean_name or email.split("@")[0][:25]
        username = base_username

        # Guarantee uniqueness
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}_{uuid.uuid4().hex[:5]}"

        user = User(
            username=username,
            email=email,
            password_hash=None,
            is_guest=False,
            target_exam=req.target_exam or "TNPSC Group 4",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Merge guest data if provided
    if req.guest_user_id:
        try:
            merge_guest_data(db, req.guest_user_id, user)
        except Exception:
            pass

    token = create_access_token({"sub": user.id, "username": user.username})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/merge", response_model=MergeResponse)
def merge_guest(
    req: MergeGuestRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Explicitly merge a guest user's bookmarks, attempts, mistakes, and progress
    into the currently authenticated student account.
    """
    guest_id = req.guest_user_id

    if not guest_id and req.guest_token:
        payload = decode_access_token(req.guest_token)
        if payload and "sub" in payload:
            guest_id = payload["sub"]

    if not guest_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either guest_user_id or guest_token must be provided",
        )

    if guest_id == user.id:
        return MergeResponse(
            merged=True,
            message="Source and target users are identical; nothing to merge.",
        )

    counts = merge_guest_data(db, guest_id, user)
    return MergeResponse(
        merged=True,
        message=f"Successfully merged guest data into student account {user.username}.",
        bookmarks_merged=counts["bookmarks"],
        attempts_merged=counts["attempts"],
        revisions_merged=counts["revisions"],
        syllabus_merged=counts["syllabus"],
    )


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    """Get profile of current authenticated student."""
    return UserResponse.model_validate(user)


@router.put("/target-exam", response_model=UserResponse)
def update_target_exam(
    req: UpdateTargetExamRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update target exam preference for the current student."""
    user.target_exam = req.target_exam
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
