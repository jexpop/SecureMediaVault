from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QMessageBox
)

from src.core.config.vault_config import (
    VaultConfig
)

from src.core.config.vault_session import (
    VaultSession
)

from src.core.crypto.key_manager import (
    KeyManager
)

from src.ui.main_window import (
    MainWindow
)


class UnlockWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Unlock Vault"
        )

        self.vault = VaultConfig()

        self.password_input = (
            QLineEdit()
        )

        self.password_input.setEchoMode(
            QLineEdit.Password
        )

        self.password_input.returnPressed.connect(
            self.unlock
        )

        self.unlock_button = (
            QPushButton("Unlock")
        )

        self.unlock_button.clicked.connect(
            self.unlock
        )

        layout = QVBoxLayout()

        layout.addWidget(
            QLabel("Password")
        )

        layout.addWidget(
            self.password_input
        )

        layout.addWidget(
            self.unlock_button
        )

        self.setLayout(layout)

    def unlock(self):

        password = (
            self.password_input.text()
        )

        ok = (
            self.vault.verify_password(
                password
            )
        )

        if not ok:

            QMessageBox.warning(
                self,
                "Error",
                "Wrong password"
            )

            return

        VaultSession.set_password(
            password
        )

        # -------------------------
        # DERIVE METADATA KEY
        # -------------------------
        key_manager = KeyManager()

        metadata_salt = (
            self.vault.get_metadata_salt()
        )

        metadata_key = key_manager.derive_key(
            password=password,
            salt=metadata_salt
        )

        VaultSession.set_metadata_key(
            metadata_key
        )

        self.main_window = (
            MainWindow()
        )

        self.main_window.show()

        self.close()