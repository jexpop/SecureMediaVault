from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QToolButton,
    QMenu,
    QWidgetAction,
    QCheckBox,
    QMessageBox
)

from PySide6.QtCore import Signal


class TagPanel(QWidget):

    # Emitted whenever the set of checked filter tags changes.
    # Carries a list of selected tag display names.
    filterChanged = Signal(list)

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

        self._filter_checkboxes = {}

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
        # FILTER (multi-select)
        # =================================================
        self.filter_button = QToolButton()

        self.filter_button.setText(
            "Filter: All"
        )

        self.filter_button.setPopupMode(
            QToolButton.InstantPopup
        )

        self.filter_menu = QMenu(
            self.filter_button
        )

        self.filter_button.setMenu(
            self.filter_menu
        )

        self.clear_filter_button = (
            QPushButton("Clear")
        )

        self.clear_filter_button.clicked.connect(
            self.clear_filters
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
            self.filter_button
        )

        layout.addWidget(
            self.clear_filter_button
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

        # Preserve the currently selected filter tags
        previously_selected = set(
            self.get_selected_filter_tags()
        )

        selected_available = (
            self.available_tags_combo
            .currentText()
        )

        self.available_tags_combo.blockSignals(
            True
        )

        self.available_tags_combo.clear()
        self.available_tags_combo.addItem("")

        # -------------------------
        # REBUILD FILTER MENU
        # -------------------------
        self.filter_menu.clear()
        self._filter_checkboxes = {}

        all_tags = (
            self.tag_service
            .get_all_tags()
        )

        for tag in all_tags:

            # Available (add existing / delete): exclude system tags
            if not tag.is_system:

                self.available_tags_combo.addItem(
                    tag.display_name
                )

            # Filter menu: include everything
            checkbox = QCheckBox(
                tag.display_name
            )

            checkbox.setChecked(
                tag.display_name in previously_selected
            )

            checkbox.stateChanged.connect(
                self._on_filter_changed
            )

            action = QWidgetAction(
                self.filter_menu
            )

            action.setDefaultWidget(
                checkbox
            )

            self.filter_menu.addAction(
                action
            )

            self._filter_checkboxes[
                tag.display_name
            ] = checkbox

        self._update_filter_button_text()

        available_index = (
            self.available_tags_combo.findText(
                selected_available
            )
        )

        if available_index >= 0:

            self.available_tags_combo.setCurrentIndex(
                available_index
            )

        self.available_tags_combo.blockSignals(
            False
        )

    # =====================================================
    # MULTI-TAG FILTER
    # =====================================================
    def get_selected_filter_tags(self):

        return [
            name
            for name, checkbox in self._filter_checkboxes.items()
            if checkbox.isChecked()
        ]

    def _update_filter_button_text(self):

        selected = (
            self.get_selected_filter_tags()
        )

        if not selected:

            self.filter_button.setText(
                "Filter: All"
            )

        elif len(selected) == 1:

            self.filter_button.setText(
                f"Filter: {selected[0]}"
            )

        else:

            self.filter_button.setText(
                f"Filter: {len(selected)} tags"
            )

    def _on_filter_changed(self, _state=None):

        self._update_filter_button_text()

        self.filterChanged.emit(
            self.get_selected_filter_tags()
        )

    def clear_filters(self):

        any_checked = False

        for checkbox in self._filter_checkboxes.values():

            if checkbox.isChecked():

                checkbox.blockSignals(True)
                checkbox.setChecked(False)
                checkbox.blockSignals(False)

                any_checked = True

        self._update_filter_button_text()

        if any_checked:

            self.filterChanged.emit([])

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
                tag.display_name
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

        success = self.tag_service.add_tag_to_media(
            self.current_media,
            tag_name
        )

        if not success:

            QMessageBox.information(
                self,
                "Reserved Tag",
                f'"{tag_name}" is reserved for automatic '
                f'image/video classification and cannot be '
                f'added manually.'
            )

            return

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

        success = self.tag_service.remove_tag_from_media(
            self.current_media,
            tag_name
        )

        if not success:

            QMessageBox.information(
                self,
                "Protected Tag",
                f'"{tag_name}" is assigned automatically '
                f'and cannot be removed.'
            )

            return

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

        success = self.tag_service.delete_tag(
            tag_name
        )

        if not success:

            QMessageBox.information(
                self,
                "Protected Tag",
                f'"{tag_name}" cannot be deleted.'
            )

            return

        self.load_tags()

        self.set_selected_media(
            self.current_media
        )

        self.refresh_callback()