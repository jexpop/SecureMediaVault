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

from PySide6.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QFont,
    QAction
)

from PySide6.QtCore import Signal, Qt


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
        tag_category_service,
        refresh_callback
    ):

        super().__init__()

        self.tag_service = tag_service
        self.tag_category_service = tag_category_service
        self.refresh_callback = refresh_callback

        self.current_media_list = []
        self._filter_checkboxes = {}
        self._mode = self.MODE_GENERAL

        self.build_ui()
        self.load_tags()
        self.set_mode(self.MODE_GENERAL)

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
        self.available_tags_button = QToolButton()
        self.available_tags_button.setText("Select tag...")
        self.available_tags_button.setPopupMode(
            QToolButton.InstantPopup
        )
        self.available_tags_button.setMinimumWidth(160)
        self.available_tags_menu = QMenu(self.available_tags_button)
        self.available_tags_button.setMenu(self.available_tags_menu)
        self._selected_delete_tag = ""

        # =================================================
        # AVAILABLE TAGS (selection mode - Add Tag)
        # =================================================
        self.selection_available_button = QToolButton()
        self.selection_available_button.setText("Select tag...")
        self.selection_available_button.setPopupMode(
            QToolButton.InstantPopup
        )
        self.selection_available_button.setMinimumWidth(160)
        self.selection_available_menu = QMenu(
            self.selection_available_button
        )
        self.selection_available_button.setMenu(
            self.selection_available_menu
        )
        self._selected_add_tag = ""

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
            self.available_tags_button,
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
            self.selection_available_button,
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
    # LOAD GLOBAL TAGS (grouped by category)
    # =====================================================
    def load_tags(self):

        previously_selected = set(
            self.get_selected_filter_tags()
        )

        # Reset available selections (tag may no longer exist)
        self._selected_add_tag = ""
        self._selected_delete_tag = ""

        self.selection_available_button.setText("Select tag...")
        self.available_tags_button.setText("Select tag...")

        # -------------------------
        # Fetch data
        # -------------------------
        categories = (
            self.tag_category_service
            .get_all_categories()
        )

        uncategorised = (
            self.tag_category_service
            .get_uncategorised_tags()
        )

        system_tags = [
            t for t in self.tag_service.get_all_tags()
            if t.is_system
        ]

        # -------------------------
        # Rebuild filter menu (QMenu with submenus per category)
        # -------------------------
        self.filter_menu.clear()
        self._filter_checkboxes = {}

        def _add_filter_tag(tag, menu):
            checkbox = QCheckBox(tag.display_name)
            checkbox.setChecked(
                tag.display_name in previously_selected
            )
            checkbox.stateChanged.connect(
                self._on_filter_changed
            )
            action = QWidgetAction(menu)
            action.setDefaultWidget(checkbox)
            menu.addAction(action)
            self._filter_checkboxes[tag.display_name] = checkbox

        # System tags at top (flat)
        for tag in system_tags:
            _add_filter_tag(tag, self.filter_menu)

        if system_tags and (categories or uncategorised):
            self.filter_menu.addSeparator()

        # Categories as submenus
        for cat in categories:
            cat_tags = (
                self.tag_category_service
                .get_tags_for_category(cat)
            )
            if not cat_tags:
                continue
            submenu = QMenu(cat.display_name, self.filter_menu)
            for tag in cat_tags:
                _add_filter_tag(tag, submenu)
            self.filter_menu.addMenu(submenu)

        # Uncategorised flat
        if uncategorised:
            if categories:
                self.filter_menu.addSeparator()
            for tag in uncategorised:
                _add_filter_tag(tag, self.filter_menu)

        self._update_filter_button_text()

        # -------------------------
        # Rebuild Available menus (grouped by category)
        # -------------------------
        self._build_tag_menu(
            self.available_tags_menu,
            categories,
            uncategorised,
            self._on_delete_tag_selected
        )

        self._build_tag_menu(
            self.selection_available_menu,
            categories,
            uncategorised,
            self._on_add_tag_selected
        )

    # -------------------------
    # Helper: build grouped tag menu (for Available buttons)
    # -------------------------
    def _build_tag_menu(
        self,
        menu,
        categories,
        uncategorised,
        on_select
    ):
        """
        Populates a QMenu with tags grouped by category as
        submenus, and uncategorised tags at the bottom (flat).
        on_select(tag_name) is called when the user picks a tag.
        """

        menu.clear()

        for cat in categories:

            cat_tags = (
                self.tag_category_service
                .get_tags_for_category(cat)
            )

            if not cat_tags:
                continue

            submenu = QMenu(cat.display_name, menu)

            for tag in cat_tags:

                action = submenu.addAction(tag.display_name)
                action.triggered.connect(
                    lambda checked, n=tag.display_name: on_select(n)
                )

            menu.addMenu(submenu)

        if uncategorised:

            if categories:
                menu.addSeparator()

            for tag in uncategorised:

                action = menu.addAction(tag.display_name)
                action.triggered.connect(
                    lambda checked, n=tag.display_name: on_select(n)
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
    # AVAILABLE TAG SELECTION CALLBACKS
    # =====================================================
    def _on_add_tag_selected(self, tag_name: str):

        self._selected_add_tag = tag_name

        self.selection_available_button.setText(
            tag_name or "Select tag..."
        )

    def _on_delete_tag_selected(self, tag_name: str):

        self._selected_delete_tag = tag_name

        self.available_tags_button.setText(
            tag_name or "Select tag..."
        )

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
            self._selected_add_tag
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

        tag_name = self._selected_delete_tag.strip()

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