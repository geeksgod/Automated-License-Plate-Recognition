from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QHeaderView, QFrame, QMessageBox, QAbstractItemView,
    QScrollArea, QListWidget, QListWidgetItem, QStackedWidget, QDialog,
    QDialogButtonBox,QInputDialog
)
from watcher.utils.db import MongoDBManager
from config import CONFIG

class WatchlistPanel(QFrame):
    def __init__(self, mongo: MongoDBManager, parent=None):
        super().__init__(parent)
        self.mongo = mongo
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("WATCHLIST MANAGEMENT")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search regos on the watchlist…")
        self.search_input.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_input)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Rego Number", "Reason", "Date Added"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, stretch=1)

        form_row = QHBoxLayout()
        self.rego_input = QLineEdit()
        self.rego_input.setPlaceholderText("Rego e.g. ABC-123")
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("Reason e.g. Prior Drive-Off")
        add_btn = QPushButton("Add to Watchlist")
        add_btn.setObjectName("AddButton")
        add_btn.clicked.connect(self._add_entry)
        form_row.addWidget(self.rego_input)
        form_row.addWidget(self.reason_input)
        form_row.addWidget(add_btn)
        layout.addLayout(form_row)

        self.conn_label = QLabel()
        self.conn_label.setObjectName("ConnLabel")
        layout.addWidget(self.conn_label)

        self.refresh()

    def _add_entry(self):
        rego = self.rego_input.text().strip()
        reason = self.reason_input.text().strip()
        if not rego:
            QMessageBox.warning(self, "Missing Rego", "Please enter a rego number before adding.")
            return
        self.mongo.add_to_watchlist(rego, reason)
        self.rego_input.clear()
        self.reason_input.clear()
        self.refresh()

    def refresh(self):
        records = self.mongo.get_watchlist(CONFIG.database.watch_list)
        self.table.setRowCount(len(records))
        for row, rec in enumerate(records):
            date_added = rec.get("date_added", "")
            date_str = date_added.strftime("%Y-%m-%d %H:%M") if hasattr(date_added, "strftime") else str(date_added)
            self.table.setItem(row, 0, QTableWidgetItem(rec.get("rego", "")))
            self.table.setItem(row, 1, QTableWidgetItem(rec.get("reason", "")))
            self.table.setItem(row, 2, QTableWidgetItem(date_str))
        state = "MongoDB: Connected" if getattr(self.mongo, "connected", False) else "MongoDB: Offline (using mock data)"
        self.conn_label.setText(state)
        self._apply_filter(self.search_input.text())

    def _apply_filter(self, text):
        query = text.strip().upper()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            rego = item.text().upper() if item else ""
            self.table.setRowHidden(row, bool(query) and query not in rego)