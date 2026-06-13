import os

from src.core.services.media_service import MediaService
from src.core.services.integrity_service import IntegrityService


class RepairService:

    def __init__(self):

        self.media_service = MediaService()
        self.integrity_service = IntegrityService()

    def scan(self, password: str):

        media_items = self.media_service.get_all_media()

        report = {
            "ok": [],
            "missing": [],
            "corrupt": []
        }

        for media in media_items:

            if not os.path.exists(media.encrypted_path):

                report["missing"].append(media)
                continue

            status = self.integrity_service.check_media(
                media,
                password
            )

            if status == "ok":
                report["ok"].append(media)

            else:
                report["corrupt"].append(media)

        return report

    def cleanup_db(self, report):

        # eliminar entradas inválidas de DB
        for media in report["missing"] + report["corrupt"]:

            self.media_service.delete_media(media.id)