import base64
import socket
from datetime import datetime
from typing import List
from urllib.parse import urlparse

from pydantic import BaseModel, HttpUrl, field_validator

from setezor.tools.validators import (validate_base64_screenshot,
                                      validate_ip_address, validate_status)


class DNSAScreenshotItem(BaseModel):
    """Схема для элемента списка скриншотов"""

    id: str
    screenshot_id: str
    domain: str
    ip: str
    screenshot_path: str
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_db_row(
        cls,
        dns_id: str,
        created_at: datetime,
        domain: str,
        ip: str,
        screenshot_id: str,
        screenshot_path: str,
    ) -> "DNSAScreenshotItem":
        """Создает объект из данных БД"""
        return cls(
            id=dns_id,
            screenshot_id=screenshot_id,
            domain=domain,
            ip=ip,
            screenshot_path=screenshot_path,
            created_at=created_at,
        )


class DNSAScreenshotListResponse(BaseModel):
    """Схема для ответа со списком скриншотов"""

    screenshots: List[DNSAScreenshotItem]
    total: int = 0

    @classmethod
    def from_db_data(cls, screenshots_data: List) -> "DNSAScreenshotListResponse":
        """Создает ответ из данных БД"""
        screenshots = [
            DNSAScreenshotItem.from_db_row(
                dns_id, created_at, domain, ip, screenshot_id, screenshot_path
            )
            for dns_id, created_at, domain, ip, screenshot_id, screenshot_path in screenshots_data
        ]
        return cls(screenshots=screenshots, total=len(screenshots))


class DNSAScreenshotTaskPayloadValidated(BaseModel):
    """Схема для создания задачи DNS A Screenshot с валидацией"""

    agent_id: str
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        """Валидация URL"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        parsed = urlparse(v)
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain")
        return v

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, v):
        """Валидация agent_id"""
        if not v or not v.strip():
            raise ValueError("Agent ID cannot be empty")
        return v.strip()

    @property
    def domain(self) -> str:
        """Извлекает домен из URL"""
        return urlparse(self.url).netloc


class DNSAScreenshotProcessedData(BaseModel):
    """Схема для обработанных данных реструктора"""

    url: str
    domain: str
    ip: str
    screenshot_bytes: bytes
    filename: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        """Валидация URL"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        parsed = urlparse(v)
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain")
        return v

    @classmethod
    def from_restructor_data(cls, raw_result: str, url: str) -> "DNSAScreenshotProcessedData":
        """Создает валидированные данные из сырого результата"""
        screenshot_bytes = base64.b64decode(raw_result)
        domain = urlparse(url).netloc
        ip = cls._resolve_ip(domain)
        import hashlib

        filename = f"{hashlib.md5(url.encode()).hexdigest()}.png"

        return cls(
            url=url, domain=domain, ip=ip, screenshot_bytes=screenshot_bytes, filename=filename
        )

    @staticmethod
    def _resolve_ip(domain: str) -> str:
        """Резолвит IP адрес домена"""
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror:
            return "0.0.0.0"


class AgentScreenshotResult(BaseModel):
    """Схема для результата от агента"""

    url: HttpUrl
    screenshot: str
    ip: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        """Валидация URL"""
        if not str(v).startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v):
        return validate_ip_address(v)

    @field_validator("screenshot")
    @classmethod
    def validate_screenshot(cls, v):
        """Валидация base64 скриншота"""
        return validate_base64_screenshot(v)


class ScreenshotResponse(BaseModel):
    """Схема для ответа с данными скриншота"""

    id: str
    path: str

    class Config:
        from_attributes = True


class DNSAScreenshotResponse(BaseModel):
    """Схема для полного ответа после обработки"""

    status: str
    file_path: str
    saved_objects: dict

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Валидация статуса"""
        return validate_status(v)
