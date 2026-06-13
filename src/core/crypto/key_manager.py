import os
import hashlib

from argon2.low_level import hash_secret_raw, Type


class KeyManager:

    def generate_salt(self) -> bytes:
        return os.urandom(16)

    def derive_key(
        self,
        password: str,
        salt: bytes
    ) -> bytes:

        key = hash_secret_raw(
            secret=password.encode("utf-8"),
            salt=salt,
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            type=Type.ID
        )

        return key

    def generate_password_hash(
        self,
        password: str
    ) -> str:

        return hashlib.sha256(
            password.encode("utf-8")
        ).hexdigest()