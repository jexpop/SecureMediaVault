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

from src.ui.main_window import (
    MainWindow
)


class SetupWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Create Vault"
        )

        self.vault = VaultConfig()

        self.password_input = (
            QLineEdit()
        )

        self.password_input.setEchoMode(
            QLineEdit.Password
        )

        self.confirm_input = (
            QLineEdit()
        )

        self.confirm_input.setEchoMode(
            QLineEdit.Password
        )

        self.create_button = (
            QPushButton(
                "Create Vault"
            )
        )

        self.create_button.clicked.connect(
            self.create_vault
        )

        layout = QVBoxLayout()

        layout.addWidget(
            QLabel("Password")
        )

        layout.addWidget(
            self.password_input
        )

        layout.addWidget(
            QLabel("Confirm Password")
        )

        layout.addWidget(
            self.confirm_input
        )

        layout.addWidget(
            self.create_button
        )

        self.setLayout(layout)

    def create_vault(self):

        password = (
            self.password_input.text()
        )

        confirm = (
            self.confirm_input.text()
        )

        if not password:

            QMessageBox.warning(
                self,
                "Error",
                "Password required"
            )

            return

        if password != confirm:

            QMessageBox.warning(
                self,
                "Error",
                "Passwords do not match"
            )

            return

        self.vault.initialize(
            password
        )

        VaultSession.set_password(
            password
        )

        self.main_window = (
            MainWindow()
        )

        self.main_window.show()

        self.close()