import hashlib
from io import IOBase


class HashManager:

    async def get_hashed_data(self, data: IOBase, size: int = 4096) -> str:
        data_for_hash = data.read(size)
        return hashlib.sha256(data_for_hash).hexdigest()

    @classmethod
    def new_instance(cls):
        return cls()