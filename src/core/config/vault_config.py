import json
import os
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import (
    VerifyMismatchError
)


class VaultConfig:

    CONFIG_PATH = Path(
        "vault/config.json"
    )

    METADATA_SALT_SIZE = 16

    def __init__(self):

        self.ph = PasswordHasher()

    def exists(self):

        return (
            self.CONFIG_PATH.exists()
        )

    def initialize(
        self,
        password: str
    ):

        self.CONFIG_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        password_hash = (
            self.ph.hash(password)
        )

        metadata_salt = os.urandom(
            self.METADATA_SALT_SIZE
        )

        data = {
            "vault_initialized": True,
            "password_hash":
            password_hash,
            "metadata_salt":
            metadata_salt.hex()
        }

        with open(
            self.CONFIG_PATH,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )

    def verify_password(
        self,
        password: str
    ) -> bool:

        with open(
            self.CONFIG_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        try:

            self.ph.verify(
                data["password_hash"],
                password
            )

            return True

        except VerifyMismatchError:

            return False

    def get_metadata_salt(self) -> bytes:

        with open(
            self.CONFIG_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        return bytes.fromhex(
            data["metadata_salt"]
        )

    def update_credentials(
        self,
        new_password: str,
        new_metadata_salt: bytes
    ):
        """
        Updates the stored password hash and metadata salt
        after a successful password change. This should be
        called LAST, only after media files and DB metadata
        have already been re-encrypted with the new password.
        """

        with open(
            self.CONFIG_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        data["password_hash"] = (
            self.ph.hash(new_password)
        )

        data["metadata_salt"] = (
            new_metadata_salt.hex()
        )

        with open(
            self.CONFIG_PATH,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )