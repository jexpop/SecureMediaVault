from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QMessageBox
)


class TagPanel(QWidget):

    def __init__(
        self,
        tag_service,
        refresh_callback
    ):

        super().__init__()

        self.tag_service = (
            tag_service
        )

        self.refresh_callback = (
            refresh_callback
        )

        self.current_media = None

        self.build_ui()

        self.load_tags()

    # =====================================================
    # UI
    # =====================================================
    def build_ui(self):

        layout = (
            QHBoxLayout()
        )

        # =================================================
        # FILTER
        # =================================================
        self.filter_combo = (
            QComboBox()
        )

        self.filter_combo.setMinimumWidth(
            160
        )

        # =================================================
        # IMAGE TAGS
        # =================================================
        self.image_tags_combo = (
            QComboBox()
        )

        self.image_tags_combo.setMinimumWidth(
            160
        )

        # =================================================
        # AVAILABLE TAGS
        # =================================================
        self.available_tags_combo = (
            QComboBox()
        )

        self.available_tags_combo.setMinimumWidth(
            160
        )

        # =================================================
        # NEW TAG
        # =================================================
        self.new_tag_input = (
            QLineEdit()
        )

        self.new_tag_input.setPlaceholderText(
            "Create new tag..."
        )

        # =================================================
        # BUTTONS
        # =================================================
        self.add_button = (
            QPushButton(
                "Add Tag"
            )
        )

        self.remove_button = (
            QPushButton(
                "Remove Selected"
            )
        )

        self.delete_button = (
            QPushButton(
                "Delete Tag"
            )
        )

        # =================================================
        # EVENTS
        # =================================================
        self.add_button.clicked.connect(
            self.add_tag
        )

        self.remove_button.clicked.connect(
            self.remove_tag
        )

        self.delete_button.clicked.connect(
            self.delete_tag
        )

        # =================================================
        # LAYOUT
        # =================================================
        layout.addWidget(
            QLabel("Filter:")
        )

        layout.addWidget(
            self.filter_combo
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            QLabel("Image Tags:")
        )

        layout.addWidget(
            self.image_tags_combo
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            QLabel("Available:")
        )

        layout.addWidget(
            self.available_tags_combo
        )

        layout.addWidget(
            QLabel("New:")
        )

        layout.addWidget(
            self.new_tag_input
        )

        layout.addWidget(
            self.add_button
        )

        layout.addWidget(
            self.remove_button
        )

        layout.addWidget(
            self.delete_button
        )

        self.setLayout(
            layout
        )

    # =====================================================
    # LOAD GLOBAL TAGS
    # =====================================================
    def load_tags(self):

        current_filter = (
            self.filter_combo
            .currentText()
        )

        selected_available = (
            self.available_tags_combo
            .currentText()
        )

        self.filter_combo.blockSignals(
            True
        )

        self.available_tags_combo.blockSignals(
            True
        )

        self.filter_combo.clear()
        self.filter_combo.addItem("")

        self.available_tags_combo.clear()
        self.available_tags_combo.addItem("")

        all_tags = (
            self.tag_service
            .get_all_tags()
        )

        for tag in all_tags:

            self.filter_combo.addItem(
                tag.name
            )

            self.available_tags_combo.addItem(
                tag.name
            )

        filter_index = (
            self.filter_combo.findText(
                current_filter
            )
        )

        if filter_index >= 0:

            self.filter_combo.setCurrentIndex(
                filter_index
            )

        available_index = (
            self.available_tags_combo.findText(
                selected_available
            )
        )

        if available_index >= 0:

            self.available_tags_combo.setCurrentIndex(
                available_index
            )

        self.filter_combo.blockSignals(
            False
        )

        self.available_tags_combo.blockSignals(
            False
        )

    # =====================================================
    # SET SELECTED MEDIA
    # =====================================================
    def set_selected_media(
        self,
        media
    ):

        self.current_media = (
            media
        )

        self.image_tags_combo.clear()
        self.image_tags_combo.addItem("")

        if not media:
            return

        tags = (
            self.tag_service
            .get_tags_for_media(
                media.id
            )
        )

        for tag in tags:

            self.image_tags_combo.addItem(
                tag.name
            )

    # =====================================================
    # ADD TAG
    # =====================================================
    def add_tag(self):

        if not self.current_media:
            return

        current_tags = (
            self.tag_service
            .get_tags_for_media(
                self.current_media.id
            )
        )

        if len(current_tags) >= 20:

            QMessageBox.warning(
                self,
                "Limit",
                "Max 20 tags per image"
            )

            return

        new_tag = (
            self.new_tag_input
            .text()
            .strip()
            .lower()
        )

        existing_tag = (
            self.available_tags_combo
            .currentText()
            .strip()
            .lower()
        )

        tag_name = None

        if new_tag:

            if len(new_tag) > 30:

                QMessageBox.warning(
                    self,
                    "Limit",
                    "Tag max length is 30"
                )

                return

            tag_name = new_tag

        elif existing_tag:

            tag_name = existing_tag

        if not tag_name:
            return

        self.tag_service.add_tag_to_media(
            self.current_media,
            tag_name
        )

        self.new_tag_input.clear()

        self.load_tags()

        self.set_selected_media(
            self.current_media
        )

        self.refresh_callback()

    # =====================================================
    # REMOVE TAG
    # =====================================================
    def remove_tag(self):

        if not self.current_media:
            return

        tag_name = (
            self.image_tags_combo
            .currentText()
            .strip()
        )

        if not tag_name:
            return

        self.tag_service.remove_tag_from_media(
            self.current_media,
            tag_name
        )

        self.set_selected_media(
            self.current_media
        )

        self.refresh_callback()

    # =====================================================
    # DELETE TAG
    # =====================================================
    def delete_tag(self):

        tag_name = (
            self.available_tags_combo
            .currentText()
            .strip()
        )

        if not tag_name:
            return

        # Check if tag has associated media
        if self.tag_service.tag_has_media(tag_name):

            media_count = len(
                self.tag_service
                .get_media_by_tag(
                    tag_name
                )
            )

            QMessageBox.warning(
                self,
                "Cannot Delete Tag",
                f'Cannot delete tag "{tag_name}" '
                f'because it is assigned to '
                f'{media_count} image(s).\n\n'
                f'Remove the tag from all images first.'
            )

            return

        # Confirm deletion if tag has no media
        result = (
            QMessageBox.question(
                self,
                "Delete Tag",
                f'Delete tag "{tag_name}" '
                f'(no images assigned)?',
                QMessageBox.Yes |
                QMessageBox.No
            )
        )

        if result != QMessageBox.Yes:
            return

        self.tag_service.delete_tag(
            tag_name
        )

        self.load_tags()

        self.set_selected_media(
            self.current_media
        )

        self.refresh_callback()
