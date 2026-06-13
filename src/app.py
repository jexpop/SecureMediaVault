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

from src.database.db_bootstrap import DBBootstrap
from src.core.config.vault_config import VaultConfig


def main():

    app = QApplication(sys.argv)

    # 1. DB bootstrap automático
    db = DBBootstrap()
    db.ensure_tables()

    # 2. Vault check
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