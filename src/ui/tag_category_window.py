from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSplitter,
    QGroupBox
)

from PySide6.QtCore import Qt, Signal


class TagCategoryWindow(QWidget):
    """
    Management window for tag categories.

    Left panel: list of categories + create/rename/delete.
    Right panel: tags in the selected category + assign/unassign.

    Emits categoriesChanged when any change is made, so
    MainWindow/TagPanel can refresh their dropdowns.
    """

    categoriesChanged = Signal()

    def __init__(
        self,
        tag_service,
        tag_category_service,
        parent=None
    ):

        super().__init__(parent)

        self.tag_service = tag_service
        self.tag_category_service = tag_category_service

        self.setWindowTitle("Manage Tag Categories")
        self.resize(700, 500)

        self._selected_category = None

        self._build_ui()
        self._load_categories()

    # =====================================================
    # UI
    # =====================================================
    def _build_ui(self):

        # -------------------------
        # LEFT: categories
        # -------------------------
        left = QGroupBox("Categories")
        left_layout = QVBoxLayout()

        self.category_list = QListWidget()
        self.category_list.currentItemChanged.connect(
            self._on_category_selected
        )

        left_layout.addWidget(self.category_list)

        cat_buttons = QHBoxLayout()

        self.new_cat_input = QLineEdit()
        self.new_cat_input.setPlaceholderText("New category name...")

        self.btn_create = QPushButton("Create")
        self.btn_create.clicked.connect(self._create_category)

        self.btn_rename = QPushButton("Rename")
        self.btn_rename.clicked.connect(self._rename_category)
        self.btn_rename.setEnabled(False)

        self.btn_delete_cat = QPushButton("Delete")
        self.btn_delete_cat.clicked.connect(self._delete_category)
        self.btn_delete_cat.setEnabled(False)
        self.btn_delete_cat.setStyleSheet(
            "QPushButton { color: #c0392b; }"
        )

        cat_buttons.addWidget(self.new_cat_input)
        cat_buttons.addWidget(self.btn_create)
        cat_buttons.addWidget(self.btn_rename)
        cat_buttons.addWidget(self.btn_delete_cat)

        left_layout.addLayout(cat_buttons)

        left.setLayout(left_layout)

        # -------------------------
        # RIGHT: tags in category
        # -------------------------
        right = QGroupBox("Tags in selected category")
        right_layout = QVBoxLayout()

        self.category_tags_list = QListWidget()

        right_layout.addWidget(
            QLabel("Tags in this category:")
        )

        right_layout.addWidget(self.category_tags_list)

        self.btn_unassign = QPushButton(
            "← Remove from category"
        )
        self.btn_unassign.clicked.connect(self._unassign_tag)
        self.btn_unassign.setEnabled(False)

        right_layout.addWidget(self.btn_unassign)

        right_layout.addWidget(
            QLabel("Uncategorised tags:")
        )

        self.uncategorised_list = QListWidget()

        right_layout.addWidget(self.uncategorised_list)

        self.btn_assign = QPushButton(
            "→ Add to category"
        )
        self.btn_assign.clicked.connect(self._assign_tag)
        self.btn_assign.setEnabled(False)

        right_layout.addWidget(self.btn_assign)

        right.setLayout(right_layout)

        # -------------------------
        # SPLITTER
        # -------------------------
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([280, 420])

        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    # =====================================================
    # LOAD CATEGORIES
    # =====================================================
    def _load_categories(self):

        current_id = (
            self._selected_category.id
            if self._selected_category
            else None
        )

        self.category_list.clear()

        categories = (
            self.tag_category_service
            .get_all_categories()
        )

        for cat in categories:

            item = QListWidgetItem(cat.display_name)
            item.setData(Qt.UserRole, cat)
            self.category_list.addItem(item)

            if current_id and cat.id == current_id:
                self.category_list.setCurrentItem(item)

        if not self.category_list.currentItem():
            self._selected_category = None
            self._load_tags_for_category(None)
            self.btn_rename.setEnabled(False)
            self.btn_delete_cat.setEnabled(False)

    # =====================================================
    # LOAD TAGS
    # =====================================================
    def _load_tags_for_category(self, category):

        self.category_tags_list.clear()
        self.uncategorised_list.clear()

        self.btn_unassign.setEnabled(False)
        self.btn_assign.setEnabled(bool(category))

        if category:

            tags = (
                self.tag_category_service
                .get_tags_for_category(category)
            )

            for tag in tags:
                item = QListWidgetItem(tag.display_name)
                item.setData(Qt.UserRole, tag)
                self.category_tags_list.addItem(item)

            self.category_tags_list.itemClicked.connect(
                lambda _: self.btn_unassign.setEnabled(True)
            )

        uncategorised = (
            self.tag_category_service
            .get_uncategorised_tags()
        )

        for tag in uncategorised:
            item = QListWidgetItem(tag.display_name)
            item.setData(Qt.UserRole, tag)
            self.uncategorised_list.addItem(item)

    # =====================================================
    # CATEGORY SELECTED
    # =====================================================
    def _on_category_selected(self, current, previous):

        if current is None:
            self._selected_category = None
            self._load_tags_for_category(None)
            self.btn_rename.setEnabled(False)
            self.btn_delete_cat.setEnabled(False)
            return

        cat = current.data(Qt.UserRole)
        self._selected_category = cat

        self.new_cat_input.setText(cat.display_name)

        self.btn_rename.setEnabled(True)
        self.btn_delete_cat.setEnabled(True)

        self._load_tags_for_category(cat)

    # =====================================================
    # CREATE CATEGORY
    # =====================================================
    def _create_category(self):

        name = self.new_cat_input.text().strip()

        if not name:
            return

        result = (
            self.tag_category_service
            .create_category(name)
        )

        if result is None:

            QMessageBox.warning(
                self,
                "Duplicate",
                f'A category named "{name}" already exists.'
            )

            return

        self.new_cat_input.clear()
        self._load_categories()
        self.categoriesChanged.emit()

    # =====================================================
    # RENAME CATEGORY
    # =====================================================
    def _rename_category(self):

        if not self._selected_category:
            return

        new_name = self.new_cat_input.text().strip()

        if not new_name:
            return

        success = (
            self.tag_category_service
            .rename_category(
                self._selected_category,
                new_name
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Duplicate",
                f'A category named "{new_name}" already exists.'
            )

            return

        self._load_categories()
        self.categoriesChanged.emit()

    # =====================================================
    # DELETE CATEGORY
    # =====================================================
    def _delete_category(self):

        if not self._selected_category:
            return

        name = self._selected_category.display_name

        tags = (
            self.tag_category_service
            .get_tags_for_category(
                self._selected_category
            )
        )

        msg = f'Delete category "{name}"?'

        if tags:
            msg += (
                f'\n\n{len(tags)} tag(s) will become '
                f'uncategorised.'
            )

        result = QMessageBox.question(
            self,
            "Delete Category",
            msg,
            QMessageBox.Yes | QMessageBox.No
        )

        if result != QMessageBox.Yes:
            return

        self.tag_category_service.delete_category(
            self._selected_category
        )

        self._selected_category = None
        self._load_categories()
        self.categoriesChanged.emit()

    # =====================================================
    # ASSIGN TAG TO CATEGORY
    # =====================================================
    def _assign_tag(self):

        if not self._selected_category:
            return

        item = self.uncategorised_list.currentItem()

        if not item:
            return

        tag = item.data(Qt.UserRole)

        self.tag_category_service.assign_tag(
            tag,
            self._selected_category
        )

        self._load_tags_for_category(
            self._selected_category
        )

        self.categoriesChanged.emit()

    # =====================================================
    # UNASSIGN TAG FROM CATEGORY
    # =====================================================
    def _unassign_tag(self):

        item = self.category_tags_list.currentItem()

        if not item:
            return

        tag = item.data(Qt.UserRole)

        self.tag_category_service.unassign_tag(tag)

        self._load_tags_for_category(
            self._selected_category
        )

        self.categoriesChanged.emit()

    # =====================================================
    # CLOSE
    # =====================================================
    def closeEvent(self, event):
        event.accept()
