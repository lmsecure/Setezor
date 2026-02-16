
from base64 import b64decode

class SnmpParser:
    @classmethod
    def parse_community_strings_file(cls, file) -> set:
        if not file:
            return []
        data = b64decode(file.split(',')[1]).decode()
        return set(data.splitlines())
