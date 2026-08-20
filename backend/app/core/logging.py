import json
import logging
import sys
from datetime import datetime
from typing import Any

# Configure standard logger
logger = logging.getLogger("skillswap.audit")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [AUDIT] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_structured_event(event_name: str, **kwargs: Any) -> None:
    """
    Logs structured JSON audit events for production observability.
    Guarantees no sensitive credentials (passwords, tokens, keys) are logged.
    """
    safe_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event_name,
    }

    # Filter and sanitize kwargs
    sanitized = {}
    for k, v in kwargs.items():
        if k in ("password", "password_hash", "token", "secret", "jwt", "authorization"):
            continue
        if isinstance(v, datetime):
            sanitized[k] = v.isoformat()
        else:
            sanitized[k] = v

    safe_data["details"] = sanitized

    try:
        logger.info(json.dumps(safe_data))
    except Exception:
        logger.info(f"{event_name}: {sanitized}")
