from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class Cryptor:
    @classmethod
    def encrypt(cls, data: bytes, key: str):
        bytes_key = bytes.fromhex(key)
        cipher = AES.new(bytes_key, AES.MODE_ECB)
        data = pad(data, AES.block_size)
        return cipher.encrypt(data)

    @classmethod
    def decrypt(cls, data: bytes, key: str):
        bytes_key = bytes.fromhex(key)
        cipher = AES.new(bytes_key, AES.MODE_ECB)
        deciphered_data = cipher.decrypt(data)
        return unpad(deciphered_data, AES.block_size)
