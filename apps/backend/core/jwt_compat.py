"""JWT compatibility layer for handling both PyJWT and python-jose."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import PyJWT first, then fall back to python-jose
jwt_available = False
jose_available = False

try:
    import jwt
    jwt_available = True
    logger.info("Using PyJWT for JWT operations")
except ImportError:
    logger.warning("PyJWT not available, trying python-jose")
    try:
        from jose import jwt
        jose_available = True
        logger.info("Using python-jose for JWT operations")
    except ImportError:
        logger.error("No JWT library available! Install PyJWT or python-jose")
        raise ImportError(
            "No JWT library found. Install either 'PyJWT' or 'python-jose[cryptography]'"
        )

# Export the working jwt module
if jwt_available or jose_available:
    __all__ = ['jwt']
else:
    raise ImportError("No JWT implementation available")


def get_jwt_library():
    """Get information about which JWT library is being used."""
    if jwt_available:
        return {"library": "PyJWT", "module": jwt}
    elif jose_available:
        return {"library": "python-jose", "module": jwt}
    else:
        raise ImportError("No JWT implementation available")


def encode_jwt(payload: Dict[str, Any], secret: str, algorithm: str = "HS256") -> str:
    """Encode JWT token with compatibility layer."""
    try:
        if jwt_available:
            # PyJWT style
            return jwt.encode(payload, secret, algorithm=algorithm)
        elif jose_available:
            # python-jose style
            return jwt.encode(payload, secret, algorithm=algorithm)
    except Exception as e:
        logger.error(f"JWT encoding failed: {e}")
        raise


def decode_jwt(token: str, secret: str, algorithms: list = None) -> Dict[str, Any]:
    """Decode JWT token with compatibility layer."""
    if algorithms is None:
        algorithms = ["HS256"]

    try:
        if jwt_available:
            # PyJWT style
            return jwt.decode(token, secret, algorithms=algorithms)
        elif jose_available:
            # python-jose style
            return jwt.decode(token, secret, algorithms=algorithms)
    except Exception as e:
        logger.error(f"JWT decoding failed: {e}")
        raise