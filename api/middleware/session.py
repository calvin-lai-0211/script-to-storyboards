"""
Session management for user authentication using Redis.
"""
import json
import logging
import time
from typing import Dict, Optional, Any

import redis
from utils.config import REDIS_CONFIG, SESSION_CONFIG

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Redis-based session manager for user authentication.
    Falls back to in-memory storage if Redis is unavailable.
    """

    def __init__(self, redis_config: Dict[str, Any], session_config: Dict[str, Any]):
        """
        Initialize SessionManager.

        Args:
            redis_config: Redis connection configuration
            session_config: Session timeout and prefix configuration
        """
        self._redis_config = redis_config
        self._session_timeout = session_config["timeout"]
        self._key_prefix = session_config["key_prefix"]
        self._redis_client: Optional[redis.Redis] = None
        self._fallback_sessions: Dict[str, Dict[str, Any]] = {}
        self._use_fallback = False

        self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection with error handling."""
        try:
            self._redis_client = redis.Redis(**self._redis_config)
            # Test connection
            self._redis_client.ping()
            logger.info("Redis connection established successfully")
            self._use_fallback = False
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}. Using in-memory fallback.")
            self._use_fallback = True
            self._redis_client = None

    def _get_key(self, session_id: str) -> str:
        """Get Redis key with prefix."""
        return f"{self._key_prefix}{session_id}"

    def set_user_session(self, session_id: str, user_data: Dict[str, Any]) -> None:
        """
        Store user session data.

        Args:
            session_id: Unique session identifier
            user_data: User information and token data
        """
        session_data = {
            "data": user_data,
            "created_at": time.time(),
            "last_accessed": time.time()
        }

        if self._use_fallback:
            self._fallback_sessions[session_id] = session_data
        else:
            try:
                key = self._get_key(session_id)
                self._redis_client.setex(
                    key,
                    self._session_timeout,
                    json.dumps(session_data)
                )
            except Exception as e:
                logger.error(f"Error setting session in Redis: {str(e)}")
                # Fall back to in-memory storage
                self._use_fallback = True
                self._fallback_sessions[session_id] = session_data

    def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user session data.

        Args:
            session_id: Session identifier

        Returns:
            User session data if valid, None otherwise
        """
        if self._use_fallback:
            return self._get_fallback_session(session_id)

        try:
            key = self._get_key(session_id)
            data = self._redis_client.get(key)

            if not data:
                return None

            session = json.loads(data)
            current_time = time.time()

            # Check if session has expired
            if current_time - session["created_at"] > self._session_timeout:
                self.delete_session(session_id)
                return None

            # Update last accessed time and extend TTL
            session["last_accessed"] = current_time
            self._redis_client.setex(
                key,
                self._session_timeout,
                json.dumps(session)
            )

            return session["data"]

        except Exception as e:
            logger.error(f"Error getting session from Redis: {str(e)}")
            # Try fallback
            return self._get_fallback_session(session_id)

    def _get_fallback_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session from in-memory fallback storage."""
        if session_id not in self._fallback_sessions:
            return None

        session = self._fallback_sessions[session_id]
        current_time = time.time()

        # Check if session has expired
        if current_time - session["created_at"] > self._session_timeout:
            del self._fallback_sessions[session_id]
            return None

        # Update last accessed time
        session["last_accessed"] = current_time
        return session["data"]

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found
        """
        if self._use_fallback:
            if session_id in self._fallback_sessions:
                del self._fallback_sessions[session_id]
                return True
            return False

        try:
            key = self._get_key(session_id)
            result = self._redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting session from Redis: {str(e)}")
            # Try fallback
            if session_id in self._fallback_sessions:
                del self._fallback_sessions[session_id]
                return True
            return False

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions (only for fallback storage).
        Redis handles expiration automatically.

        Returns:
            Number of sessions removed
        """
        if self._use_fallback:
            current_time = time.time()
            expired_sessions = [
                session_id
                for session_id, session in self._fallback_sessions.items()
                if current_time - session["created_at"] > self._session_timeout
            ]

            for session_id in expired_sessions:
                del self._fallback_sessions[session_id]

            return len(expired_sessions)

        return 0


# Global session manager instance
session_manager = SessionManager(REDIS_CONFIG, SESSION_CONFIG)
