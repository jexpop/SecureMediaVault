from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QListWidget,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QListWidgetItem,
    QMessageBox
)

from PySide6.QtGui import (
    QIcon
)

from PySide6.QtCore import (
    QSize,
    Qt
)

from src.core.services.import_service import (
    ImportService
)

from src.core.services.media_service import (
    MediaService
)

from src.core.services.thumbnail_service import (
    ThumbnailService
)

from src.core.services.integrity_service import (
    IntegrityService
)

from src.core.services.tag_service import (
    TagService
)

from src.core.services.delete_service import (
    DeleteService
)

from src.core.services.media_category import (
    classify_extension
)

from src.core.config.vault_session import (
    VaultSession
)

from src.ui.preview_window import (
    PreviewWindow
)

from src.ui.video_player_window import (
    VideoPlayerWindow
)

from src.ui.widgets.tag_panel import (
    TagPanel
)

from src.ui.change_password_window import (
    ChangePasswordWindow
)


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Secure Media Vault"
        )

        self.resize(
            1200,
            800
        )

        self.current_media_items = []

        # =====================================================
        # SERVICES
        # =====================================================
        self.import_service = (
            ImportService()
        )

        self.media_service = (
            MediaService()
        )

        self.thumbnail_service = (
            ThumbnailService()
        )

        self.integrity_service = (
            IntegrityService()
        )

        self.tag_service = (
            TagService()
        )

        self.delete_service = (
            DeleteService()
        )

        # =====================================================
        # IMPORT BUTTON
        # =====================================================
        self.import_button = (
            QPushButton(
                "Import File"
            )
        )

        self.import_button.clicked.connect(
            self.import_file
        )

        # =====================================================
        # DELETE BUTTON
        # =====================================================
        self.delete_button = (
            QPushButton(
                "Delete Selected"
            )
        )

        self.delete_button.clicked.connect(
            self.delete_selected_media
        )

        # =====================================================
        # CHANGE PASSWORD BUTTON
        # =====================================================
        self.change_password_button = (
            QPushButton(
                "Change Password"
            )
        )

        self.change_password_button.clicked.connect(
            self.open_change_password
        )

        # =====================================================
        # GALLERY
        # =====================================================
        self.gallery = QListWidget()

        self.gallery.setViewMode(
            QListWidget.IconMode
        )

        self.gallery.setIconSize(
            QSize(180, 180)
        )

        self.gallery.setGridSize(
            QSize(220, 240)
        )

        self.gallery.setResizeMode(
            QListWidget.Adjust
        )

        self.gallery.setSpacing(
            12
        )

        self.gallery.itemDoubleClicked.connect(
            self.open_preview
        )

        self.gallery.itemSelectionChanged.connect(
            self.on_media_selected
        )

        # =====================================================
        # TAG PANEL
        # =====================================================
        self.tag_panel = (
            TagPanel(
                tag_service=
                self.tag_service,

                refresh_callback=
                self.refresh_current_view
            )
        )

        self.tag_panel.filterChanged.connect(
            self.on_filter_changed
        )

        # =====================================================
        # MAIN LAYOUT
        # =====================================================
        layout = (
            QVBoxLayout()
        )

        layout.addWidget(
            self.import_button
        )

        layout.addWidget(
            self.delete_button
        )

        layout.addWidget(
            self.change_password_button
        )

        layout.addWidget(
            self.tag_panel
        )

        layout.addWidget(
            self.gallery
        )

        container = QWidget()

        container.setLayout(
            layout
        )

        self.setCentralWidget(
            container
        )

        self.preview_window = None
        self.video_player_window = None
        self.change_password_window = None

        self.load_media()

    # =====================================================
    # CHANGE PASSWORD
    # =====================================================
    def open_change_password(self):

        self.change_password_window = (
            ChangePasswordWindow()
        )

        self.change_password_window.show()

    # =====================================================
    # MEDIA SELECTED
    # =====================================================
    def on_media_selected(self):

        item = (
            self.gallery
            .currentItem()
        )

        if not item:

            self.tag_panel.set_selected_media(
                None
            )

            return

        media = item.data(
            Qt.UserRole
        )

        self.tag_panel.set_selected_media(
            media
        )

    # =====================================================
    # FILTER CHANGED (multi-tag, AND)
    # =====================================================
    def on_filter_changed(
        self,
        tag_names
    ):

        if not tag_names:

            self.load_media()

        else:

            self.filter_by_tags(
                tag_names
            )

    # =====================================================
    # FORMAT TAGS
    # =====================================================
    def format_tags(
        self,
        tags
    ):

        if not tags:

            return "[untagged]"

        names = [
            t.display_name
            for t in tags
        ]

        max_visible = 6

        visible = names[
            :max_visible
        ]

        text = " • ".join(
            visible
        )

        remaining = (
            len(names)
            - max_visible
        )

        if remaining > 0:

            text += (
                f" +{remaining}"
            )

        return text

    # =====================================================
    # POPULATE GALLERY ITEM
    # =====================================================
    def _populate_gallery_item(self, media, password):

        item = QListWidgetItem()

        tags = (
            self.tag_service
            .get_tags_for_media(
                media.id
            )
        )

        item.setText(
            self.format_tags(
                tags
            )
        )

        item.setToolTip(
            media.display_filename
        )

        pixmap = (
            self.thumbnail_service
            .get_gallery_pixmap(
                media=media,
                password=password
            )
        )

        item.setIcon(
            QIcon(
                pixmap
            )
        )

        item.setData(
            Qt.UserRole,
            media
        )

        self.gallery.addItem(
            item
        )

    # =====================================================
    # LOAD MEDIA
    # =====================================================
    def load_media(self):

        self.gallery.clear()

        password = (
            VaultSession
            .get_password()
        )

        media_items = (
            self.media_service
            .get_all_media()
        )

        self.current_media_items = (
            media_items
        )

        for media in media_items:

            status = (
                self.integrity_service
                .check_media(
                    media,
                    password
                )
            )

            if status != "ok":
                continue

            self._populate_gallery_item(
                media,
                password
            )

    # =====================================================
    # REFRESH VIEW
    # =====================================================
    def refresh_current_view(self):

        selected_tags = (
            self.tag_panel
            .get_selected_filter_tags()
        )

        if selected_tags:

            self.filter_by_tags(
                selected_tags
            )

        else:

            self.load_media()

    # =====================================================
    # IMPORT FILE
    # =====================================================
    def import_file(self):

        file_path, _ = (
            QFileDialog
            .getOpenFileName(
                self,
                "Select file"
            )
        )

        if not file_path:
            return

        password = (
            VaultSession
            .get_password()
        )

        self.import_service.import_file(
            source_file=file_path,
            password=password
        )

        self.refresh_current_view()

    # =====================================================
    # DELETE SELECTED MEDIA
    # =====================================================
    def delete_selected_media(self):

        item = (
            self.gallery
            .currentItem()
        )

        if not item:

            QMessageBox.warning(
                self,
                "No Selection",
                "Please select an image to delete"
            )

            return

        media = item.data(
            Qt.UserRole
        )

        # Confirmation dialog
        result = (
            QMessageBox.warning(
                self,
                "Delete Media",
                f'Are you sure you want to permanently '
                f'delete "{media.display_filename}"?\n\n'
                f'This action cannot be undone.\n'
                f'The file, database record, and all tags '
                f'will be removed.',
                QMessageBox.Yes |
                QMessageBox.No
            )
        )

        if result != QMessageBox.Yes:
            return

        # Delete media
        success = (
            self.delete_service
            .delete_media(
                media
            )
        )

        if success:

            # Cleanup empty folders
            self.delete_service.cleanup_empty_folders()

            QMessageBox.information(
                self,
                "Success",
                "Media deleted successfully"
            )

            self.refresh_current_view()

        else:

            QMessageBox.critical(
                self,
                "Error",
                "Failed to delete media"
            )

    # =====================================================
    # FILTER BY TAGS (AND - must have ALL selected tags)
    # =====================================================
    def filter_by_tags(
        self,
        tag_names
    ):

        self.gallery.clear()

        password = (
            VaultSession
            .get_password()
        )

        media_items = (
            self.tag_service
            .get_media_by_tags(
                tag_names
            )
        )

        media_items = (
            self.media_service
            .decorate_media_list(
                media_items
            )
        )

        self.current_media_items = (
            media_items
        )

        for media in media_items:

            self._populate_gallery_item(
                media,
                password
            )

    # =====================================================
    # PREVIEW / PLAYBACK
    # =====================================================
    def open_preview(
        self,
        item
    ):

        media = item.data(
            Qt.UserRole
        )

        password = (
            VaultSession
            .get_password()
        )

        category = classify_extension(
            media.display_media_type
        )

        # -------------------------
        # VIDEO -> REUSABLE PLAYER WINDOW
        # -------------------------
        if category == "video":

            if self.video_player_window is None:

                self.video_player_window = (
                    VideoPlayerWindow()
                )

            self.video_player_window.load_media(
                media=media,
                password=password
            )

            self.video_player_window.show()
            self.video_player_window.raise_()
            self.video_player_window.activateWindow()

            return

        # -------------------------
        # IMAGE -> PREVIEW (navigate within images only)
        # -------------------------
        image_items = [
            m for m in self.current_media_items
            if classify_extension(m.display_media_type) == "image"
        ]

        current_index = 0

        for i, m in enumerate(
            image_items
        ):

            if m.id == media.id:

                current_index = i
                break

        self.preview_window = (
            PreviewWindow(
                media_list=
                image_items,

                current_index=
                current_index,

                password=
                password
            )
        )

        self.preview_window.show()