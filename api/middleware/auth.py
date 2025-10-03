"""
Authentication middleware and dependency functions for FastAPI.
"""
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from api.middleware.session import session_manager


class UserPrincipal:
    """Represents an authenticated user."""

    def __init__(self, user_data: Optional[Dict[str, Any]] = None):
        self.data = user_data or {}
        self.is_authenticated = user_data is not None

    def get(self, key: str, default=None):
        """Get a value from user data."""
        return self.data.get(key, default)

    def __getitem__(self, key: str):
        """Allow dict-like access to user data."""
        return self.data[key]

    def __bool__(self):
        """Check if user is authenticated."""
        return self.is_authenticated


def get_session_id_from_request(request: Request) -> Optional[str]:
    """
    Extract session ID from request cookies or headers.

    Args:
        request: FastAPI request object

    Returns:
        Session ID if found, None otherwise
    """
    # Try to get session ID from cookie first
    session_id = request.cookies.get("st_sess_id")

    if not session_id:
        # Fallback to Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_id = auth_header.split(" ", 1)[1]

    return session_id


async def get_current_user(request: Request) -> UserPrincipal:
    """
    Dependency function to get current user (optional).
    Returns UserPrincipal with is_authenticated=False if not logged in.

    Args:
        request: FastAPI request object

    Returns:
        UserPrincipal instance
    """
    session_id = get_session_id_from_request(request)

    if not session_id:
        return UserPrincipal(None)

    user_session = session_manager.get_user_session(session_id)

    if not user_session:
        return UserPrincipal(None)

    # Extract user data from session
    user_data = user_session.get("user", {})
    return UserPrincipal(user_data)


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


async def require_auth(request: Request) -> UserPrincipal:
    """
    Dependency function that requires authentication.
    Returns 4003 error with Google auth URL if user is not authenticated.

    Args:
        request: FastAPI request object

    Returns:
        UserPrincipal instance

    Raises:
        AuthenticationError: If user is not authenticated (code 4003 or 4004)
    """
    user = await get_current_user(request)

    if not user.is_authenticated:
        # 获取 Google 登录地址
        from api.routes.google_auth import get_google_auth_url
        referer = request.headers.get("Referer", "/")
        auth_url = get_google_auth_url(referer)

        # 抛出自定义认证错误
        raise AuthenticationError(
            code=4003,
            message="未登录或登录已过期，请重新登录",
            data={"auth_url": auth_url}
        )

    # Check user status
    user_status = user.get("status", 0)
    if user_status != 1:
        raise AuthenticationError(
            code=4004,
            message="账号状态异常，请联系管理员",
            data=None
        )

    return user
