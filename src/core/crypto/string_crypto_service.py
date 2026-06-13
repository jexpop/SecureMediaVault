import os
import base64
import hmac
import hashlib

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


class StringCryptoService:
    """
    Encrypts/decrypts short strings (filenames, tag names, etc.)
    using a pre-derived AES-256 key (the "metadata key").

    Unlike EncryptionService (used for media files), this service
    does NOT derive a new key per call via Argon2 - it expects an
    already-derived 32-byte key, so it can be used cheaply for many
    small fields (DB metadata) without repeating expensive Argon2
    work on every read/write.
    """

    HEADER = b"SMVS1"

    def encrypt(self, plaintext: str, key: bytes) -> str:

        aesgcm = AESGCM(key)

        nonce = os.urandom(12)

        ciphertext = aesgcm.encrypt(
            nonce,
            plaintext.encode("utf-8"),
            None
        )

        blob = self.HEADER + nonce + ciphertext

        return base64.urlsafe_b64encode(blob).decode("ascii")

    def decrypt(self, token: str, key: bytes) -> str:

        blob = base64.urlsafe_b64decode(token.encode("ascii"))

        header = blob[:len(self.HEADER)]

        if header != self.HEADER:
            raise Exception("Invalid encrypted string format")

        nonce = blob[len(self.HEADER):len(self.HEADER) + 12]
        ciphertext = blob[len(self.HEADER) + 12:]

        aesgcm = AESGCM(key)

        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        except InvalidTag:
            raise Exception("Wrong password or corrupted data")

        return plaintext.decode("utf-8")

    def hash_value(self, value: str, key: bytes) -> str:
        """
        Deterministic HMAC-SHA256 hash, used for lookups/uniqueness
        (e.g. tag names) without storing the value in clear.
        """
        return hmac.new(
            key,
            value.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()