import hashlib

from fastapi import UploadFile


class UploadFileHashManager:

    async def get_hashed_data(self, data: UploadFile, size=4096) -> str:
        await data.seek(0)
        data_for_hash = await data.read(size)
        return hashlib.sha256(data_for_hash).hexdigest()

    @classmethod
    def new_instance(cls):
        return cls()