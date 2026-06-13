import os

# Silence FFmpeg/Qt Multimedia's verbose stream-info logging
# (e.g. "Input #0, mov,mp4...", stream/codec details) that
# gets printed to the console every time a video is opened.
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg=false"

from PySide6.QtWidgets import (
    QApplication
)

import sys

from src.core.config.vault_config import (
    VaultConfig
)

from src.ui.unlock_window import (
    UnlockWindow
)

from src.ui.setup_window import (
    SetupWindow
)

from src.core.services.temp_media_service import (
    TempMediaService
)

from src.database.db_bootstrap import DBBootstrap
from src.core.config.vault_config import VaultConfig


def main():

    app = QApplication(sys.argv)

    # 1. DB bootstrap automático
    db = DBBootstrap()
    db.ensure_tables()

    # 2. Limpieza de ficheros temporales descifrados de una
    #    sesión anterior (p. ej. si la app se cerró de forma
    #    abrupta sin borrar el vídeo temporal).
    TempMediaService().cleanup_stale()

    # 3. Vault check
    vault = VaultConfig()

    if vault.exists():
        from src.ui.unlock_window import UnlockWindow
        window = UnlockWindow()
    else:
        from src.ui.setup_window import SetupWindow
        window = SetupWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()