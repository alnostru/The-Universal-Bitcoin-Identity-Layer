"""
Storage backend for HODLXXI.

This is an in-memory implementation suitable for development and testing.
For production, replace with Redis/PostgreSQL backed storage.
"""
import logging
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)

# In-memory storage dictionaries
_CLIENTS: Dict[str, dict] = {}
_AUTH_CODES: Dict[str, dict] = {}
_SESSIONS: Dict[str, dict] = {}
_REFRESH_TOKENS: Dict[str, dict] = {}


def init_storage():
    """Initialize the storage backend."""
    log.info("Storage backend: in-memory demo (not persistent).")
    log.warning("⚠️  In-memory storage is for development only. Data will be lost on restart.")


class Storage:
    """
    Storage interface for HODLXXI.

    This implementation uses in-memory dictionaries for simplicity.
    For production, implement Redis or PostgreSQL backends.
    """

    def save_client(self, client_id: str, data: dict) -> None:
        """Save OAuth2 client data."""
        _CLIENTS[client_id] = data
        log.debug(f"Saved client: {client_id}")

    def get_client(self, client_id: str) -> Optional[dict]:
        """Retrieve OAuth2 client data."""
        return _CLIENTS.get(client_id)

    def delete_client(self, client_id: str) -> None:
        """Delete OAuth2 client data."""
        if client_id in _CLIENTS:
            del _CLIENTS[client_id]
            log.debug(f"Deleted client: {client_id}")

    def save_auth_code(self, code: str, data: dict) -> None:
        """Save authorization code (temporary, should expire)."""
        _AUTH_CODES[code] = data
        log.debug(f"Saved auth code: {code[:8]}...")

    def pop_auth_code(self, code: str) -> Optional[dict]:
        """Retrieve and remove authorization code (one-time use)."""
        data = _AUTH_CODES.pop(code, None)
        if data:
            log.debug(f"Consumed auth code: {code[:8]}...")
        return data

    def save_session(self, session_id: str, data: dict) -> None:
        """Save user session data."""
        _SESSIONS[session_id] = data
        log.debug(f"Saved session: {session_id[:8]}...")

    def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve user session data."""
        return _SESSIONS.get(session_id)

    def delete_session(self, session_id: str) -> None:
        """Delete user session."""
        if session_id in _SESSIONS:
            del _SESSIONS[session_id]
            log.debug(f"Deleted session: {session_id[:8]}...")

    def save_refresh_token(self, token: str, data: dict) -> None:
        """Save refresh token data."""
        _REFRESH_TOKENS[token] = data
        log.debug(f"Saved refresh token: {token[:8]}...")

    def get_refresh_token(self, token: str) -> Optional[dict]:
        """Retrieve refresh token data."""
        return _REFRESH_TOKENS.get(token)

    def delete_refresh_token(self, token: str) -> None:
        """Delete refresh token."""
        if token in _REFRESH_TOKENS:
            del _REFRESH_TOKENS[token]
            log.debug(f"Deleted refresh token: {token[:8]}...")

    def save(self, key: str, value: Any) -> None:
        """Generic save operation."""
        # For now, store in sessions dict
        _SESSIONS[key] = value

    def get(self, key: str) -> Optional[Any]:
        """Generic get operation."""
        return _SESSIONS.get(key)

    def delete(self, key: str) -> None:
        """Generic delete operation."""
        if key in _SESSIONS:
            del _SESSIONS[key]


def get_storage() -> Storage:
    """Get the storage instance."""
    return Storage()
