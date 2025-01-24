import os
import datetime
import jwt

SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
ALGORITHM = "HS256"  # Алгоритм для подписи
ACCESS_TOKEN_EXPIRE_MINUTES = datetime.timedelta(days=7)
REFRESH_TOKEN_EXPIRE_MINUTES = datetime.timedelta(days=30)


class JWTManager:
    @classmethod
    def create_access_token(cls, data: dict):
        return cls.create_jwt(data=data, expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES)

    @classmethod
    def create_refresh_token(cls, data: dict):
        return cls.create_jwt(data=data, expires_delta=REFRESH_TOKEN_EXPIRE_MINUTES)

    @classmethod
    def create_jwt(cls, data: dict, expires_delta: datetime.timedelta):
        to_encode = data.copy()
        expire = datetime.datetime.now(tz=datetime.timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @classmethod
    def is_expired(cls, token: str):
        try:
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return False
        except:
            return True
    
    @classmethod
    def get_payload(cls, token: str) -> dict:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except:
            return None
