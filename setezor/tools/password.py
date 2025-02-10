from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
rounds = 300_000


class PasswordTool:
    @classmethod
    def hash(cls, plain_password: str):
        return pwd_context.hash(plain_password, rounds=rounds)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str):
        return pwd_context.verify(plain_password, hashed_password)
