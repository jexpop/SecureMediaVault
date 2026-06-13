from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QProgressBar,
    QMessageBox
)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.core.services.password_change_service import (
    PasswordChangeService
)


class ChangePasswordWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Change Master Password"
        )

        self.service = PasswordChangeService()

        # -------------------------
        # WARNING
        # -------------------------
        warning_label = QLabel(
            "This will re-encrypt your entire vault.\n"
            "It is strongly recommended to back up the\n"
            "'vault' folder before continuing.\n"
            "Do not close the app while this is running."
        )

        # -------------------------
        # INPUTS
        # -------------------------
        self.current_input = QLineEdit()
        self.current_input.setEchoMode(QLineEdit.Password)

        self.new_input = QLineEdit()
        self.new_input.setEchoMode(QLineEdit.Password)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)

        # -------------------------
        # PROGRESS
        # -------------------------
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        # -------------------------
        # BUTTON
        # -------------------------
        self.change_button = QPushButton(
            "Change Password"
        )

        self.change_button.clicked.connect(
            self.handle_change_password
        )

        # -------------------------
        # LAYOUT
        # -------------------------
        layout = QVBoxLayout()

        layout.addWidget(warning_label)

        layout.addWidget(QLabel("Current password"))
        layout.addWidget(self.current_input)

        layout.addWidget(QLabel("New password"))
        layout.addWidget(self.new_input)

        layout.addWidget(QLabel("Confirm new password"))
        layout.addWidget(self.confirm_input)

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.change_button)

        self.setLayout(layout)

    def handle_change_password(self):

        current = self.current_input.text()
        new = self.new_input.text()
        confirm = self.confirm_input.text()

        if not current or not new or not confirm:

            QMessageBox.warning(
                self,
                "Error",
                "All fields are required"
            )

            return

        if new != confirm:

            QMessageBox.warning(
                self,
                "Error",
                "New passwords do not match"
            )

            return

        if new == current:

            QMessageBox.warning(
                self,
                "Error",
                "New password must be different "
                "from the current one"
            )

            return

        # Final confirmation
        result = QMessageBox.question(
            self,
            "Confirm",
            "Are you sure you want to change the master "
            "password? Make sure you have a backup of the "
            "'vault' folder.",
            QMessageBox.Yes | QMessageBox.No
        )

        if result != QMessageBox.Yes:
            return

        self.change_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        def on_progress(current_i, total):

            if total > 0:
                percent = int((current_i / total) * 100)
            else:
                percent = 100

            self.progress_bar.setValue(percent)

            # Keep the UI responsive during the (long) operation.
            QApplication.processEvents()

        try:

            self.service.change_password(
                old_password=current,
                new_password=new,
                progress_callback=on_progress
            )

            QMessageBox.information(
                self,
                "Success",
                "Password changed successfully."
            )

            self.close()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Password change failed:\n{e}\n\n"
                f"If the vault appears broken, restore "
                f"it from your backup."
            )

            self.change_button.setEnabled(True)
            self.progress_bar.setVisible(False)