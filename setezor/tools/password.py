from passlib.context import CryptContext
from setezor.settings import PASSWORD_HASH_ROUNDS

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class PasswordTool:
    @classmethod
    def hash(cls, plain_password: str):
        return pwd_context.hash(plain_password, rounds=PASSWORD_HASH_ROUNDS)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str):
        return pwd_context.verify(plain_password, hashed_password)
