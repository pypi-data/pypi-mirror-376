__all__ = [
    "install", "ok", "err", 
    "event", "event_login", "event_logout", "event_register", 
    "event_password_change", "event_password_reset", 
    "__version__"
]

__version__ = "0.1.0"

from .wrap import (
    install, ok, err, 
    event, event_login, event_logout, event_register, 
    event_password_change, event_password_reset
)
