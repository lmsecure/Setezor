import os
import datetime
import jwt

from setezor.settings import ACCESS_TOKEN_EXPIRE_TIME, ALGORITHM, REFRESH_TOKEN_EXPIRE_TIME, SECRET_KEY




class JWT_Tool:
    @classmethod
    def create_access_token(cls, data: dict):
        return cls.create_jwt(data=data, expires_delta=ACCESS_TOKEN_EXPIRE_TIME)

    @classmethod
    def create_refresh_token(cls, data: dict):
        return cls.create_jwt(data=data, expires_delta=REFRESH_TOKEN_EXPIRE_TIME)

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
