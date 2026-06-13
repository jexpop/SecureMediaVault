from pathlib import Path

from src.core.crypto.encryption_service import (
    EncryptionService
)


class ExportService:

    def __init__(self):

        self.encryption_service = (
            EncryptionService()
        )

    def decrypt_to_temp(
        self,
        encrypted_path: str,
        output_path: str,
        password: str
    ):

        encrypted = Path(
            encrypted_path
        )

        if not encrypted.exists():

            raise Exception(
                "Encrypted file not found"
            )

        output = Path(output_path)

        output.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.encryption_service.decrypt_file(
            source_path=str(encrypted),
            target_path=str(output),
            password=password
        )

        return str(output)