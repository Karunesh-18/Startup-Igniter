"""
db/__init__.py — exposes the public DB surface.
"""

from db.database import Base, close_db, get_db, get_engine, get_session_factory
from db import models  # noqa: F401  — ensures models are registered on Base

__all__ = [
    "Base",
    "close_db",
    "get_db",
    "get_engine",
    "get_session_factory",
    "models",
]
