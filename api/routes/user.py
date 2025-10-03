"""
User management routes.
"""
import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from api.middleware.auth import get_current_user, UserPrincipal
from api.routes.google_auth import get_google_auth_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/check-login")
async def check_login_status(
    request: Request,
    user: UserPrincipal = Depends(get_current_user)
):
    """
    Check user login status.

    Args:
        request: FastAPI request object
        user: Current user principal

    Returns:
        JSON response with user status and auth URL if not logged in
    """
    try:
        if not user or not user.is_authenticated:
            # Get current page URL from Referer header
            referer = request.headers.get("Referer", "/")
            auth_url = get_google_auth_url(referer)

            return JSONResponse(
                status_code=401,
                content={
                    "code": 401,
                    "message": "User not logged in or session expired",
                    "data": {"auth_url": auth_url}
                }
            )

        # Return user information
        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "message": "User is logged in",
                "data": {"user": user.data}
            }
        )

    except Exception as e:
        logger.error(f"Error checking login status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": f"Failed to check login status: {str(e)}",
                "data": None
            }
        )


@router.post("/logout")
async def logout(request: Request, user: UserPrincipal = Depends(get_current_user)):
    """
    Logout user by clearing session.

    Args:
        request: FastAPI request object
        user: Current user principal

    Returns:
        JSON response indicating logout success
    """
    try:
        from api.middleware.auth import get_session_id_from_request
        from api.middleware.session import session_manager

        session_id = get_session_id_from_request(request)
        if session_id:
            session_manager.delete_session(session_id)

        response = JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "message": "Logout successful",
                "data": None
            }
        )

        # Clear cookie
        response.delete_cookie(key="st_sess_id", path="/")

        return response

    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": f"Logout failed: {str(e)}",
                "data": None
            }
        )
