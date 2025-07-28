"""
Утилиты для валидации данных
"""

import base64
import ipaddress


def validate_ip_address(v: str) -> str:
    """Валидация IP адреса"""
    try:
        ipaddress.ip_address(v)
        return v
    except ValueError:
        raise ValueError("Invalid IP address format")


def validate_base64_screenshot(v: str) -> str:
    """Валидация base64 скриншота"""
    try:
        base64.b64decode(v)
        return v
    except Exception:
        raise ValueError("Invalid base64 encoded screenshot")


def validate_status(v: str) -> str:
    """Валидация статуса"""
    allowed_statuses = ["success", "error"]
    if v not in allowed_statuses:
        raise ValueError(f"Status must be one of: {allowed_statuses}")
    return v
