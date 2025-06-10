"""
Lean PDF Editor – Qt front-end
Now with “Add Text” mode to place arbitrary text anywhere on a page.
"""

from __future__ import annotations

# ---------- Qt imports ----------
from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QLabel,
    QToolBar,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QInputDialog,
)
from PySide6.QtGui import QAction, QPixmap, QImage
from PySide6.QtCore import Qt, QEvent, QObject

# ---------- Local ----------
from pdf_engine import PDFEngine


class PDFEditor(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lean PDF Editor")
        self.resize(900, 700)

        self.engine: PDFEngine | None = None
        self.add_text_mode: bool = False  # toggled by toolbar button

        self._create_actions()
        self._create_ui()

    # ===== UI scaffolding ==================================================
    def _create_actions(self):
        # File actions
        self.open_action = QAction("Open PDF", self)
        self.open_action.triggered.connect(self.open_file)

        self.save_action = QAction("Save As", self)
        self.save_action.triggered.connect(self.save_file)
        self.save_action.setEnabled(False)

        # Form-field editor
        self.fields_action = QAction("Edit Form Fields", self)
        self.fields_action.triggered.connect(self.open_fields_dialog)
        self.fields_action.setEnabled(False)

        # Add-text mode
        self.text_action = QAction("Add Text", self)
        self.text_action.setCheckable(True)
        self.text_action.toggled.connect(self.toggle_add_text)
        self.text_action.setEnabled(False)

    def _create_ui(self):
        # Menu
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)

        # Toolbar
        tb = QToolBar("Main")
        self.addToolBar(tb)
        tb.addAction(self.open_action)
        tb.addAction(self.save_action)
        tb.addAction(self.fields_action)
        tb.addAction(self.text_action)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        vbox = QVBoxLayout(central)

        # Page display label
        self.page_label = QLabel(alignment=Qt.AlignCenter)
        self.page_label.setText("Open a PDF to start editing.")
        self.page_label.installEventFilter(self)  # intercept clicks
        vbox.addWidget(self.page_label, stretch=1)

        # Navigation controls
        nav = QHBoxLayout()
        self.prev_btn = QPushButton("Prev")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)

        self.page_spin = QSpinBox()
        self.page_spin.setEnabled(False)
        self.page_spin.setMinimum(1)
        self.page_spin.valueChanged.connect(self.goto_page)

        nav.addWidget(self.prev_btn)
        nav.addWidget(self.next_btn)
        nav.addWidget(self.page_spin)
        vbox.addLayout(nav)

    # ===== File handling ===================================================
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            self.engine = PDFEngine(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open PDF:\n{e}")
            return

        # Enable previously disabled controls
        total = self.engine.page_count()
        self.page_spin.setMaximum(total)
        for w in (
            self.prev_btn,
            self.next_btn,
            self.page_spin,
            self.save_action,
            self.fields_action,
            self.text_action,
        ):
            w.setEnabled(True)

        self.show_page(0)

    def save_file(self):
        if not self.engine:
            return
        out, _ = QFileDialog.getSaveFileName(self, "Save PDF As", "", "PDF Files (*.pdf)")
        if not out:
            return
        try:
            self.engine.save(out)
            QMessageBox.information(self, "Saved", "PDF saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save:\n{e}")

    # ===== Page navigation & rendering ====================================
    def show_page(self, index: int):
        """Render page *index* into the QLabel."""
        if not self.engine:
            return
        self.engine.current_page = index
        pix = self.engine.render_page(index, zoom=1.5)
        fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        self.page_label.setPixmap(
            QPixmap.fromImage(img).scaled(
                self.page_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        # Sync spinbox without recursion
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(index + 1)
        self.page_spin.blockSignals(False)

    def resizeEvent(self, ev):
        if self.engine:
            self.show_page(self.engine.current_page)
        super().resizeEvent(ev)

    def prev_page(self):
        if self.engine and self.engine.current_page > 0:
            self.show_page(self.engine.current_page - 1)

    def next_page(self):
        if self.engine and self.engine.current_page < self.engine.page_count() - 1:
            self.show_page(self.engine.current_page + 1)

    def goto_page(self, val: int):
        if self.engine:
            self.show_page(val - 1)

    # ===== Add-text mode ===================================================
    def toggle_add_text(self, checked: bool):
        """Enable/disable free-text insertion mode."""
        self.add_text_mode = checked
        self.setCursor(Qt.CrossCursor if checked else Qt.ArrowCursor)

    def eventFilter(self, obj: QObject, ev: QEvent) -> bool:
        """Intercept clicks on the page label when in add-text mode."""
        if (
            obj is self.page_label
            and self.add_text_mode
            and self.engine
            and ev.type() == QEvent.MouseButtonPress
            and ev.button() == Qt.LeftButton
        ):
            self._handle_add_text_click(ev.position().toPoint())
            return True  # event consumed
        return super().eventFilter(obj, ev)

    def _handle_add_text_click(self, pos_label):
        """Convert label coords → PDF coords and insert text."""
        pixmap = self.page_label.pixmap()
        if not pixmap:
            return

        # Prompt user for the text content
        text, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
        if not (ok and text):
            return

        # Convert label position to position inside the pixmap
        lab_w, lab_h = self.page_label.width(), self.page_label.height()
        pm_w, pm_h = pixmap.width(), pixmap.height()
        # Centered pixmap inside label – find offsets
        offset_x = (lab_w - pm_w) // 2
        offset_y = (lab_h - pm_h) // 2
        x_in_pixmap = pos_label.x() - offset_x
        y_in_pixmap = pos_label.y() - offset_y
        if not (0 <= x_in_pixmap <= pm_w and 0 <= y_in_pixmap <= pm_h):
            return  # click was in padding area

        # Map to PDF coordinate space
        page = self.engine.doc.load_page(self.engine.current_page)
        pdf_w, pdf_h = page.rect.width, page.rect.height
        x_pdf = x_in_pixmap * (pdf_w / pm_w)
        y_pdf = y_in_pixmap * (pdf_h / pm_h)

        # Insert text at the mapped coordinates (default 12 pt)
        self.engine.insert_text(self.engine.current_page, x_pdf, y_pdf, text)
        self.show_page(self.engine.current_page)  # refresh

    # ===== Form-field dialog ==============================================
    def open_fields_dialog(self):
        if not self.engine:
            return
        fields = self.engine.list_form_fields()
        if not fields:
            QMessageBox.information(self, "No Fields", "This PDF has no form fields.")
            return

        dlg = FieldsDialog(fields, self)
        if dlg.exec() == QDialog.Accepted:
            for name, value in dlg.get_updates().items():
                self.engine.update_form_field(name, value)
            self.show_page(self.engine.current_page)


class FieldsDialog(QDialog):
    """Simple table UI for editing form-field values."""

    def __init__(self, fields: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Form Fields")
        self.resize(500, 400)
        self._updates: dict[str, str] = {}

        vbox = QVBoxLayout(self)

        self.table = QTableWidget(len(fields), 2)
        self.table.setHorizontalHeaderLabels(["Field", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )

        for row, f in enumerate(fields):
            name_item = QTableWidgetItem(f["name"])
            name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(str(f["value"] or "")))

        vbox.addWidget(self.table)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        vbox.addWidget(btns)

    def accept(self):
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            val = self.table.item(row, 1).text()
            self._updates[name] = val
        super().accept()

    def get_updates(self) -> dict[str, str]:
        return self._updates
