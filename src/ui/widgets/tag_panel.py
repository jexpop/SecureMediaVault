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

    # Emitted when tags of a specific media item change
    # (add/remove). Carries the list of media_ids affected.
    tagChanged = Signal(list)

    MODE_GENERAL = "general"
    MODE_SELECTION = "selection"

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

        self.current_media_list = []

        self._filter_checkboxes = {}
        self._mode = self.MODE_GENERAL

        self.build_ui()

        self.load_tags()

        self.set_mode(
            self.MODE_GENERAL
        )

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
        # AVAILABLE TAGS (global, general mode - Delete Tag)
        # =================================================
        self.available_tags_combo = (
            QComboBox()
        )

        self.available_tags_combo.setMinimumWidth(
            160
        )

        # =================================================
        # AVAILABLE TAGS (selection mode - Add Tag)
        # =================================================
        self.selection_available_combo = (
            QComboBox()
        )

        self.selection_available_combo.setMinimumWidth(
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
        # GENERAL MODE GROUP
        # (filter + global tag management: Available + Delete Tag)
        # =================================================
        self.general_widgets = [
            QLabel("Filter:"),
            self.filter_button,
            self.clear_filter_button,
            QLabel("Available:"),
            self.available_tags_combo,
            self.delete_button,
        ]

        for w in self.general_widgets:
            layout.addWidget(w)

        # =================================================
        # SELECTION MODE GROUP
        # (per-item tag management)
        # =================================================
        self.selection_widgets = [
            QLabel("Image Tags:"),
            self.image_tags_combo,
            QLabel("Available:"),
            self.selection_available_combo,
            QLabel("New:"),
            self.new_tag_input,
            self.add_button,
            self.remove_button,
        ]

        for w in self.selection_widgets:
            layout.addWidget(w)

        self.setLayout(
            layout
        )

    # =====================================================
    # MODE SWITCHING
    # =====================================================
    def set_mode(self, mode):

        self._mode = mode

        is_general = (
            mode == self.MODE_GENERAL
        )

        for w in self.general_widgets:
            w.setVisible(is_general)

        for w in self.selection_widgets:
            w.setVisible(not is_general)

    def get_mode(self):

        return self._mode

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

        selected_selection_available = (
            self.selection_available_combo
            .currentText()
        )

        self.available_tags_combo.blockSignals(
            True
        )

        self.selection_available_combo.blockSignals(
            True
        )

        self.available_tags_combo.clear()
        self.available_tags_combo.addItem("")

        self.selection_available_combo.clear()
        self.selection_available_combo.addItem("")

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

                self.selection_available_combo.addItem(
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

        for combo, previous_text in (
            (self.available_tags_combo, selected_available),
            (self.selection_available_combo, selected_selection_available),
        ):

            index = combo.findText(
                previous_text
            )

            if index >= 0:
                combo.setCurrentIndex(index)

        self.available_tags_combo.blockSignals(
            False
        )

        self.selection_available_combo.blockSignals(
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
    # SET SELECTED MEDIA (list, supports multi-selection)
    # =====================================================
    def set_selected_media_list(
        self,
        media_list
    ):
        """
        Updates the Image Tags combo to reflect the tags of all
        selected items. Tags present in ALL selected items appear
        normally. Tags present in only SOME of them appear with
        a "(partial)" suffix so the user knows they're not
        universal across the selection.
        """

        self.current_media_list = media_list or []

        self.image_tags_combo.clear()
        self.image_tags_combo.addItem("")

        if not self.current_media_list:
            return

        count = len(self.current_media_list)

        # Build a dict: tag_display_name -> how many items have it
        tag_counts = {}

        for media in self.current_media_list:

            tags = (
                self.tag_service
                .get_tags_for_media(
                    media.id
                )
            )

            for tag in tags:

                name = tag.display_name

                tag_counts[name] = (
                    tag_counts.get(name, 0) + 1
                )

        # Sort: system tags first, then alpha (mirrors tag_service)
        all_tag_names = sorted(
            tag_counts.keys(),
            key=lambda n: (
                not any(
                    t.is_system
                    for media in self.current_media_list
                    for t in self.tag_service.get_tags_for_media(
                        media.id
                    )
                    if t.display_name == n
                ),
                n
            )
        )

        for name in all_tag_names:

            c = tag_counts[name]

            if c == count:
                # All selected items have this tag
                self.image_tags_combo.addItem(name)
            else:
                # Only some items have it
                self.image_tags_combo.addItem(
                    f"{name} (partial {c}/{count})"
                )

    # =====================================================
    # GET SELECTED TAG NAME (strips "(partial ...)" suffix)
    # =====================================================
    def _get_selected_image_tag_name(self):
        """
        Returns the clean tag name from the Image Tags combo,
        stripping the "(partial N/M)" suffix if present.
        """

        raw = self.image_tags_combo.currentText().strip()

        if " (partial " in raw:
            return raw.split(" (partial ")[0].strip()

        return raw

    # =====================================================
    # ADD TAG (to all selected items)
    # =====================================================
    def add_tag(self):

        if not self.current_media_list:
            return

        new_tag = (
            self.new_tag_input
            .text()
            .strip()
            .lower()
        )

        existing_tag = (
            self.selection_available_combo
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

        affected_ids = []
        reserved_error = False

        for media in self.current_media_list:

            current_tags = (
                self.tag_service
                .get_tags_for_media(media.id)
            )

            if len(current_tags) >= 20:
                continue

            success = self.tag_service.add_tag_to_media(
                media,
                tag_name
            )

            if success:
                affected_ids.append(media.id)
            else:
                reserved_error = True

        if reserved_error and not affected_ids:

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

        self.set_selected_media_list(
            self.current_media_list
        )

        if affected_ids:
            self.tagChanged.emit(affected_ids)

    # =====================================================
    # REMOVE TAG (from all selected items that have it)
    # =====================================================
    def remove_tag(self):

        if not self.current_media_list:
            return

        tag_name = self._get_selected_image_tag_name()

        if not tag_name:
            return

        affected_ids = []
        protected_error = False

        for media in self.current_media_list:

            # Only attempt removal from items that have this tag
            existing = [
                t.display_name
                for t in self.tag_service.get_tags_for_media(
                    media.id
                )
            ]

            if tag_name not in existing:
                continue

            success = self.tag_service.remove_tag_from_media(
                media,
                tag_name
            )

            if success:
                affected_ids.append(media.id)
            else:
                protected_error = True

        if protected_error and not affected_ids:

            QMessageBox.information(
                self,
                "Protected Tag",
                f'"{tag_name}" is assigned automatically '
                f'and cannot be removed.'
            )

            return

        self.set_selected_media_list(
            self.current_media_list
        )

        if affected_ids:
            self.tagChanged.emit(affected_ids)

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

        self.set_selected_media_list(
            self.current_media_list
        )

        self.refresh_callback()