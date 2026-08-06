import base64

from Cryptodome import Random
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHA1
from Cryptodome.Protocol.KDF import PBKDF2
from django.conf import settings


class AESCipher:
    def __init__(self, salt: str):
        assert AES.block_size == 16
        self.bs = AES.block_size
        self.key: bytes = PBKDF2(settings.ENCRYPTION_KEY.encode(), salt.encode(), 32, 65536, hmac_hash_module=SHA1)

    def encrypt(self, plaintext: str) -> str:
        value: bytes = self.pad(plaintext).encode('utf-8')
        iv: bytes = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(value)).decode('utf-8')

    def decrypt(self, cipher_text: str) -> str:
        cipher_text: bytes = base64.b64decode(cipher_text.encode('utf-8'))
        iv: bytes = cipher_text[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.unpad(cipher.decrypt(cipher_text[AES.block_size:])).decode('utf-8')

    def pad(self, s: str) -> str:
        return s + (self.bs - len(s.encode('utf-8')) % self.bs) * chr(self.bs - len(s.encode('utf-8')) % self.bs)

    @staticmethod
    def unpad(s: bytes) -> bytes:
        return s[:-ord(s[len(s)-1:])]
