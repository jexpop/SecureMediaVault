from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QListWidget,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QListWidgetItem,
    QMessageBox,
    QToolButton
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

from src.core.services.temp_media_service import (
    TempMediaService
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

from src.ui.widgets.video_thumbnail_widget import (
    VideoThumbnailWidget
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

        self.temp_media_service = (
            TempMediaService()
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
        # CHANGE PASSWORD BUTTON (key icon)
        # =====================================================
        self.change_password_button = (
            QToolButton()
        )

        self.change_password_button.setText(
            "\U0001F511"  # 🔑
        )

        self.change_password_button.setToolTip(
            "Change Password"
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
            QSize(220, 320)
        )

        self.gallery.setResizeMode(
            QListWidget.Adjust
        )

        self.gallery.setSpacing(
            12
        )

        self.gallery.setWordWrap(
            True
        )

        self.gallery.itemDoubleClicked.connect(
            self.open_preview
        )

        self.gallery.itemClicked.connect(
            self.on_gallery_item_clicked
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

        self.tag_panel.tagChanged.connect(
            self._update_gallery_item_tags
        )

        # =====================================================
        # MAIN LAYOUT
        # =====================================================
        self.top_bar_layout = (
            QHBoxLayout()
        )

        self.top_bar_layout.addWidget(
            self.import_button
        )

        self.top_bar_layout.addWidget(
            self.delete_button
        )

        self.top_bar_layout.addWidget(
            self.tag_panel
        )

        self.top_bar_layout.addStretch(
            1
        )

        self.top_bar_layout.addWidget(
            self.change_password_button
        )

        layout = (
            QVBoxLayout()
        )

        layout.addLayout(
            self.top_bar_layout
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
        self._previous_selected_item = None
        self._video_player_open = False
        self._preview_open = False

        self.load_media()

        self._update_top_bar_for_selection(
            None
        )

    # =====================================================
    # CHANGE PASSWORD
    # =====================================================
    def open_change_password(self):

        self.change_password_window = (
            ChangePasswordWindow()
        )

        self.change_password_window.show()

    # =====================================================
    # TOP BAR VISIBILITY BASED ON SELECTION
    # =====================================================
    def _update_top_bar_for_selection(self, media):

        has_selection = media is not None

        self.import_button.setVisible(
            not has_selection
        )

        self.delete_button.setVisible(
            has_selection
        )

        self.tag_panel.set_mode(
            TagPanel.MODE_SELECTION
            if has_selection
            else TagPanel.MODE_GENERAL
        )

    # =====================================================
    # GALLERY ITEM CLICKED (single source of truth for
    # selection toggling)
    # =====================================================
    def on_gallery_item_clicked(self, item):

        if item is self._previous_selected_item:

            # Re-click on the already-selected item -> deselect
            self._deselect_current_item()

        else:

            # New selection (or first selection)
            self._select_item(item)

    # =====================================================
    # SELECT ITEM
    # =====================================================
    def _select_item(self, item):

        # Un-highlight the previous video thumbnail (if any)
        if self._previous_selected_item is not None:

            previous_widget = (
                self.gallery.itemWidget(
                    self._previous_selected_item
                )
            )

            if isinstance(
                previous_widget,
                VideoThumbnailWidget
            ):

                previous_widget.set_selected(False)

        self._previous_selected_item = item

        media = item.data(
            Qt.UserRole
        )

        self.tag_panel.set_selected_media(
            media
        )

        self._update_top_bar_for_selection(
            media
        )

        current_widget = (
            self.gallery.itemWidget(
                item
            )
        )

        if isinstance(
            current_widget,
            VideoThumbnailWidget
        ):

            current_widget.set_selected(True)

    # =====================================================
    # DESELECT CURRENT ITEM
    # =====================================================
    def _deselect_current_item(self):

        item = self._previous_selected_item

        if item is not None:

            current_widget = (
                self.gallery.itemWidget(
                    item
                )
            )

            if isinstance(
                current_widget,
                VideoThumbnailWidget
            ):

                current_widget.set_selected(False)

        self._previous_selected_item = None

        self.gallery.blockSignals(True)
        self.gallery.clearSelection()
        self.gallery.setCurrentItem(None)
        self.gallery.blockSignals(False)

        self.tag_panel.set_selected_media(
            None
        )

        self._update_top_bar_for_selection(
            None
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

        max_visible = 16

        visible = names[
            :max_visible
        ]

        remaining = (
            len(names)
            - max_visible
        )

        if remaining > 0:

            visible.append(
                f"+{remaining} more"
            )

        # Group tags into lines of up to 6, joined by " • "
        per_line = 6

        lines = []

        for i in range(0, len(visible), per_line):

            chunk = visible[i:i + per_line]

            lines.append(
                " • ".join(chunk)
            )

        return "\n".join(lines)

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

        tags_text = self.format_tags(
            tags
        )

        item.setToolTip(
            media.display_filename
        )

        item.setData(
            Qt.UserRole,
            media
        )

        category = classify_extension(
            media.display_media_type
        )

        has_video_preview = (
            category == "video"
            and self.thumbnail_service.has_video_preview(
                media.encrypted_path
            )
        )

        self.gallery.addItem(
            item
        )

        if has_video_preview:

            static_pixmap = (
                self.thumbnail_service
                .get_video_static_pixmap(
                    media.encrypted_path,
                    password
                )
            )

            def gif_provider(
                encrypted_path=media.encrypted_path,
                password=password
            ):

                return (
                    self.thumbnail_service
                    .get_video_preview_gif_bytes(
                        encrypted_path,
                        password
                    )
                )

            thumbnail_widget = VideoThumbnailWidget(
                static_pixmap=static_pixmap,
                gif_bytes_provider=gif_provider,
                thumbnail_size=self.gallery.iconSize(),
                tags_text=tags_text
            )

            item.setSizeHint(
                self.gallery.gridSize()
            )

            self.gallery.setItemWidget(
                item,
                thumbnail_widget
            )

        else:

            item.setText(
                tags_text
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

    # =====================================================
    # UPDATE TAGS TEXT FOR A SINGLE GALLERY ITEM
    # (fast path for add_tag / remove_tag — avoids reloading
    # the whole gallery just to update one item's tag list)
    # =====================================================
    def _update_gallery_item_tags(self, media_id: int):

        for i in range(self.gallery.count()):

            item = self.gallery.item(i)

            media = item.data(Qt.UserRole)

            if media is None or media.id != media_id:
                continue

            tags = (
                self.tag_service
                .get_tags_for_media(
                    media_id
                )
            )

            new_text = self.format_tags(tags)

            widget = self.gallery.itemWidget(item)

            if widget is not None and hasattr(widget, "tags_label"):

                # VideoThumbnailWidget: update its embedded label
                widget.tags_label.setText(new_text)

            else:

                item.setText(new_text)

            break

    # =====================================================
    # LOAD MEDIA
    # =====================================================
    def load_media(self):

        self.gallery.clear()
        self._previous_selected_item = None

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
                "Select file",
                "",
                "",
                options=
                QFileDialog.DontUseNativeDialog
            )
        )

        if not file_path:
            return

        filename = (
            Path(file_path).name
        )

        if self.media_service.filename_exists(filename):

            QMessageBox.warning(
                self,
                "Duplicate File",
                f'A file named "{filename}" already exists '
                f'in the vault.\n\n'
                f'Please rename the file before importing, '
                f'or choose a different file.'
            )

            return

        password = (
            VaultSession
            .get_password()
        )

        self.import_service.import_file(
            source_file=file_path,
            password=password
        )

        self._secure_delete_original(
            file_path,
            filename
        )

        self.refresh_current_view()

    # =====================================================
    # SECURE DELETE OF ORIGINAL FILE AFTER IMPORT
    # =====================================================
    def _secure_delete_original(
        self,
        file_path,
        filename
    ):
        """
        Securely deletes the original file (overwrite + unlink)
        right after a successful import, without asking for
        confirmation.
        """

        success = (
            self.temp_media_service
            .secure_delete(
                file_path
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Error",
                f'Could not delete the original file '
                f'"{filename}".\n\n'
                f'It may be in use by another program. '
                f'You can delete it manually.'
            )

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
        self._previous_selected_item = None

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
                    VideoPlayerWindow(
                        on_close_callback=
                        self._on_media_viewer_closed
                    )
                )

            self.video_player_window.load_media(
                media=media,
                password=password
            )

            self.video_player_window.show()
            self.video_player_window.raise_()
            self.video_player_window.activateWindow()

            self._video_player_open = True

            self.change_password_button.setEnabled(
                False
            )

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
                password,

                on_close_callback=
                self._on_media_viewer_closed
            )
        )

        self.preview_window.show()

        self._preview_open = True

        self.change_password_button.setEnabled(
            False
        )

    # =====================================================
    # MEDIA VIEWER CLOSED (re-enable Change Password)
    # =====================================================
    def _on_media_viewer_closed(self, sender=None):
        """
        Called from VideoPlayerWindow/PreviewWindow's closeEvent,
        passing the window instance itself as `sender`. This lets
        us track open/closed state explicitly instead of relying
        on isVisible() (unreliable right at close time).
        """

        if sender is self.video_player_window:
            self._video_player_open = False

        elif sender is self.preview_window:
            self._preview_open = False

        if not self._video_player_open and not self._preview_open:

            self.change_password_button.setEnabled(
                True
            )