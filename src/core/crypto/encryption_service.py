from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
import os

from src.core.crypto.key_manager import KeyManager


class EncryptionService:

    HEADER = b"SMV1"

    def __init__(self):

        self.key_manager = KeyManager()

    def encrypt_file(
        self,
        source_path: str,
        target_path: str,
        password: str
    ):

        salt = self.key_manager.generate_salt()

        key = self.key_manager.derive_key(
            password=password,
            salt=salt
        )

        aesgcm = AESGCM(key)

        nonce = os.urandom(12)

        with open(source_path, "rb") as f:
            data = f.read()

        encrypted_data = aesgcm.encrypt(
            nonce,
            data,
            None
        )

        with open(target_path, "wb") as f:

            f.write(self.HEADER)
            f.write(salt)
            f.write(nonce)
            f.write(encrypted_data)

    def decrypt_bytes(
        self,
        source_path: str,
        password: str
    ) -> bytes:

        with open(
            source_path,
            "rb"
        ) as f:

            header = f.read(4)

            if header != self.HEADER:

                raise Exception(
                    "Invalid file format"
                )

            salt = f.read(16)

            nonce = f.read(12)

            encrypted_data = (
                f.read()
            )

        key = self.key_manager.derive_key(
            password=password,
            salt=salt
        )

        aesgcm = AESGCM(key)

        try:

            decrypted_data = (
                aesgcm.decrypt(
                    nonce,
                    encrypted_data,
                    None
                )
            )

        except InvalidTag:

            raise Exception(
                "Wrong password or corrupted file"
            )

        return decrypted_data
