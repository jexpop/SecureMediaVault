import json
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import (
    VerifyMismatchError
)


class VaultConfig:

    CONFIG_PATH = Path(
        "vault/config.json"
    )

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

        data = {
            "vault_initialized": True,
            "password_hash":
            password_hash
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