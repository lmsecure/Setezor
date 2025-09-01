import hashlib
from io import BytesIO, IOBase

from fastapi import UploadFile


class UploadFileHashManager:

    async def get_hashed_data(self, data: IOBase, size=4096) -> str:
        data_for_hash = data.read(size)
        return hashlib.sha256(data_for_hash).hexdigest()

    @classmethod
    def new_instance(cls):
        return cls()