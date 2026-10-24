"""Outbound-URL safety for user-supplied webhooks (SSRF guard) and token encryption."""

import base64
import hashlib
import ipaddress
import socket
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

from core.config import get_settings


def assert_public_https(url: str) -> None:
    """Only https URLs whose host resolves exclusively to public addresses."""
    u = urlparse(url)
    if u.scheme != "https" or not u.hostname:
        raise HTTPException(422, "Webhook URL must be https.")
    try:
        infos = socket.getaddrinfo(u.hostname, u.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise HTTPException(422, "Webhook host does not resolve.")
    if not all(ipaddress.ip_address(i[4][0]).is_global for i in infos):
        raise HTTPException(422, "Webhook URL must point to a public address.")


def _fernet() -> Fernet:
    s = get_settings()
    key = s.INTEGRATION_KEY.encode() if s.INTEGRATION_KEY else base64.urlsafe_b64encode(hashlib.sha256(s.SECRET_KEY.encode()).digest())
    return Fernet(key)


def seal(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def unseal(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        raise HTTPException(409, "Stored credential can no longer be decrypted; reconnect the integration.")
