from typing import Any, Dict, Optional
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from asgi_correlation_id import (
     correlation_id, 
     CorrelationIdMiddleware, 
     CorrelationIdFilter
)
import json

_event_log = logging.getLogger("cidwrap.events")

def install(app:FastAPI, 
            header_name:str = "X-Correlation-ID",
            expose_header:bool = True) -> None:
    app.add_middleware(
        CorrelationIdMiddleware,
        header_name=header_name,
        update_request_header=True,          
    )
    handler = logging.StreamHandler()
    handler.addFilter(CorrelationIdFilter())
    logging.basicConfig(
        handlers=[handler],
        level=logging.INFO,
        format="%(levelname)s [%(correlation_id)s] %(name)s: %(message)s",
    )
    if expose_header:
        try:
            from fastapi.middleware.cors import CORSMiddleware
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
                expose_headers=[header_name],
            )
        except Exception:
            pass

def ok(data: Any=None, *, message:str ="OK" , code:str="SUCCESS", 
       meta:Optional[Dict[str,Any]]=None, status:int=200)-> JSONResponse:
    return JSONResponse({
        "ok": True,
        "code": code,
        "message": message,
        "data": data,
        "meta": meta or {},
        "correlation_id": correlation_id.get(),
    }, status_code=status)

def err(*, message: str, code: str = "ERROR",
        errors: Any = None, status: int = 400) -> JSONResponse:
    return JSONResponse({
        "ok": False,
        "code": code,
        "message": message,
        "errors": errors,
        "correlation_id": correlation_id.get(),
    }, status_code=status)

def event_login(username: str) -> None:
    """Log a user login event."""
    event("auth.login", {"username": username})

def event_logout(username: str) -> None:
    """Log a user logout event."""
    event("auth.logout", {"username": username})

def event_register(username: str, email: str) -> None:
    """Log a user registration event."""
    event("auth.register", {"username": username, "email": email})

def event_password_change(username: str) -> None:
    """Log a user password change event."""
    event("auth.password_changed", {"username": username})

def event_password_reset(username: str) -> None:
    """Log a user password reset event."""
    event("auth.password_reset", {"username": username})


def event(name: str, payload: dict | None = None) -> None:
    """
    Log custom events tied to the current correlation ID.
    """
    _event_log.info(
        "event=%s cid=%s payload=%s",   
        name,                           
        correlation_id.get(),           
        payload or {},                  
    )
