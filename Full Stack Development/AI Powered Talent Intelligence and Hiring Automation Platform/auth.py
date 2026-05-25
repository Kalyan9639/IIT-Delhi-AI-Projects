"""
Authentication endpoints for HireForge Pro.
Handles Google One-Tap Login with OAuth 2.0.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import requests
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database import create_user, get_user_by_google_id, get_user_by_email, get_user_by_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# Load Google OAuth configuration from environment
GOOGLE_CLIENT_ID = os.getenv("CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("CLIENT_SECRET", "").strip()


class GoogleTokenVerifyRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    id: int
    google_id: str
    email: str
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None


def verify_google_token(id_token: str) -> dict:
    """
    Verify Google ID token and return user info.
    Uses Google's OAuth 2.0 verification endpoint.
    """
    try:
        # Google's token verification endpoint
        token_uri = "https://oauth2.googleapis.com/tokeninfo?id_token={}"
        response = requests.get(token_uri.format(id_token), timeout=10)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Google token verification failed: {response.text}")
            raise HTTPException(status_code=401, detail="Invalid Google ID token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")


def get_authenticated_user(request: Request) -> dict:
    """
    Resolve the current authenticated user from a Google ID token.

    This helper is reused by authenticated routers so they do not depend on
    request state being set by middleware.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    id_token = auth_header.split(" ", 1)[1].strip()
    google_user = verify_google_token(id_token)

    google_id = google_user.get("sub")
    if not google_id:
        raise HTTPException(status_code=401, detail="Invalid Google ID token")

    user = get_user_by_google_id(google_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/google/verify", response_model=UserResponse)
async def google_login(request: Request, payload: GoogleTokenVerifyRequest):
    """
    Google One-Tap Login endpoint.
    - For new users: Creates profile and returns user data
    - For existing users: Returns existing user data
    """
    try:
        # Verify the Google ID token
        google_user = verify_google_token(payload.id_token)

        # Extract user information from Google token
        google_id = google_user.get("sub")
        email = google_user.get("email")
        name = google_user.get("name", "")
        given_name = google_user.get("given_name")
        family_name = google_user.get("family_name")
        picture = google_user.get("picture")

        if not google_id or not email:
            raise HTTPException(status_code=400, detail="Missing required Google user information")

        # Check if user exists
        existing_user = get_user_by_google_id(google_id)

        if existing_user:
            # Return existing user
            return UserResponse(**existing_user)
        else:
            # Check if email exists (different Google accounts for same email)
            existing_by_email = get_user_by_email(email)
            if existing_by_email:
                # Update existing user with new Google ID
                import sqlite3
                conn = sqlite3.connect("hireforge_users.db")
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET google_id = ? WHERE email = ?
                ''', (google_id, email))
                conn.commit()
                conn.close()
                return UserResponse(**existing_by_email)

            # Create new user
            user_id = create_user(google_id, email, name, given_name, family_name, picture)

            return UserResponse(
                id=user_id,
                google_id=google_id,
                email=email,
                name=name,
                given_name=given_name,
                family_name=family_name,
                picture=picture
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/me")
async def get_current_user(request: Request):
    """
    Get current authenticated user from session.
    This endpoint expects a valid Google ID token in the Authorization header.
    """
    user = get_authenticated_user(request)
    return UserResponse(**user)


@router.post("/logout")
async def logout(request: Request):
    """
    Logout endpoint (client-side token invalidation).
    Google OAuth uses short-lived tokens, so server-side logout is minimal.
    """
    return {"message": "Logged out successfully. Client-side token should be cleared."}
