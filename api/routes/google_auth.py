"""
Google OAuth authentication routes.
"""
import hashlib
import logging
from typing import Optional, Dict, Any

import requests
from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

from api.middleware.session import session_manager
from utils.config import DB_CONFIG, GOOGLE_OAUTH_CONFIG, API_BASE_URL
from utils.database import Database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user/google", tags=["google_auth"])


def get_google_auth_url(state: Optional[str] = None) -> str:
    """
    Generate Google OAuth authorization URL.

    Args:
        state: Optional state parameter (typically the URL to redirect back to)

    Returns:
        Google OAuth authorization URL
    """
    # 拼接完整的 redirect_uri
    redirect_uri = f"{API_BASE_URL}{GOOGLE_OAUTH_CONFIG['redirect_path']}"

    params = {
        "client_id": GOOGLE_OAUTH_CONFIG["client_id"],
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": redirect_uri,
        "state": state or "/",
        "prompt": "consent",
    }

    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    auth_url = f"{GOOGLE_OAUTH_CONFIG['auth_url']}?{query_string}"
    return auth_url


def exchange_code_for_token(code: str) -> Optional[Dict[str, Any]]:
    """
    Exchange authorization code for access token.

    Args:
        code: Authorization code from Google

    Returns:
        Token information dict or None on error
    """
    try:
        # 拼接完整的 redirect_uri
        redirect_uri = f"{API_BASE_URL}{GOOGLE_OAUTH_CONFIG['redirect_path']}"

        token_data = {
            "code": code,
            "client_id": GOOGLE_OAUTH_CONFIG["client_id"],
            "client_secret": GOOGLE_OAUTH_CONFIG["client_secret"],
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        response = requests.post(GOOGLE_OAUTH_CONFIG["token_url"], data=token_data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error exchanging code for token: {str(e)}")
        return None


def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Get user information using access token.

    Args:
        access_token: Google access token

    Returns:
        User information dict or None on error
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(GOOGLE_OAUTH_CONFIG["user_info_url"], headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return None


def save_or_update_user(db: Database, user_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Save or update user information in database.

    Args:
        db: Database instance
        user_info: User information from Google

    Returns:
        User data dict or None on error
    """
    try:
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")

        if not google_id:
            logger.error("Google ID not found in user info")
            return None

        conn = db._get_connection()
        try:
            cur = conn.cursor()

            # Check if user exists
            check_sql = """
                SELECT id, open_id, avatar, email, name, status
                FROM users
                WHERE open_id = %s AND platform = 'google' AND is_deleted = 0
            """
            cur.execute(check_sql, (google_id,))
            row = cur.fetchone()

            if row:
                # User exists, update if needed
                columns = [desc[0] for desc in cur.description]
                user = dict(zip(columns, row))

                update_fields = []
                update_values = []

                if not user["avatar"] and picture:
                    update_fields.append("avatar = %s")
                    update_values.append(picture)
                if not user["email"] and email:
                    update_fields.append("email = %s")
                    update_values.append(email)
                if not user["name"] and name:
                    update_fields.append("name = %s")
                    update_values.append(name)

                if update_fields:
                    update_sql = f"""
                        UPDATE users
                        SET {", ".join(update_fields)}, update_time = CURRENT_TIMESTAMP
                        WHERE open_id = %s AND platform = 'google'
                    """
                    update_values.append(google_id)
                    cur.execute(update_sql, tuple(update_values))
                    conn.commit()

                # Return updated user data
                return {
                    "user_id": user["id"],
                    "open_id": google_id,
                    "platform": "google",
                    "status": user["status"],
                    "email": email or user["email"],
                    "name": name or user["name"],
                    "picture": picture or user["avatar"],
                }
            else:
                # Create new user
                insert_sql = """
                    INSERT INTO users (open_id, avatar, email, name, platform, status, is_deleted)
                    VALUES (%s, %s, %s, %s, %s, 1, 0)
                    RETURNING id
                """
                cur.execute(insert_sql, (google_id, picture, email, name, "google"))
                user_id = cur.fetchone()[0]
                conn.commit()

                return {
                    "user_id": user_id,
                    "open_id": google_id,
                    "platform": "google",
                    "status": 1,
                    "email": email,
                    "name": name,
                    "picture": picture,
                }
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    except Exception as e:
        logger.error(f"Error saving/updating user: {str(e)}")
        return None


@router.get("/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None)
):
    """
    Handle Google OAuth callback.

    Args:
        request: FastAPI request object
        code: Authorization code from Google
        state: State parameter (redirect URL)

    Returns:
        Redirect response to original URL with session cookie
    """
    try:
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code is required")

        # Exchange code for token
        token_info = exchange_code_for_token(code)
        if not token_info or "access_token" not in token_info:
            raise HTTPException(status_code=500, detail="Failed to get access token")

        # Get user information
        access_token = token_info["access_token"]
        user_info = get_user_info(access_token)
        if not user_info:
            raise HTTPException(status_code=500, detail="Failed to get user information")

        # Save or update user in database
        db = Database(DB_CONFIG)
        user = save_or_update_user(db, user_info)
        if not user:
            raise HTTPException(status_code=500, detail="Failed to save user information")

        # Check user status
        if user["status"] != 1:
            raise HTTPException(status_code=403, detail="Account status is invalid")

        # Create session
        session_id = hashlib.md5(access_token.encode()).hexdigest()
        session_data = {
            "user": user,
            "token_info": {
                "access_token": access_token,
                "expires_in": token_info.get("expires_in"),
                "refresh_token": token_info.get("refresh_token"),
            },
        }
        session_manager.set_user_session(session_id, session_data)

        # Redirect to original URL with session cookie
        redirect_url = state if state else "/"
        response = RedirectResponse(url=redirect_url, status_code=302)

        # Set cookie with appropriate flags
        # 本地开发时不设置SameSite，避免跨端口问题
        import os
        is_production = os.getenv("ENV", "development") == "production"

        response.set_cookie(
            key="st_sess_id",
            value=session_id,
            max_age=2592000,  # 30 days
            path="/",
            httponly=True,
            samesite="none" if is_production else None,  # 生产环境用none，本地开发不设置
            secure=is_production,  # 生产环境必须HTTPS
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Google callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Google login failed: {str(e)}")
