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
        self.search_input.setPlaceholderText("Search plates on the watchlist…")
        self.search_input.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_input)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Plate Number", "Amount", "Date Added", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, stretch=1)

        form_row = QHBoxLayout()
        self.plate_input = QLineEdit()
        self.plate_input.setPlaceholderText("plate e.g. ABC-123")
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("amount e.g. Prior Drive-Off")
        add_btn = QPushButton("Add to Watchlist")
        add_btn.setObjectName("AddButton")
        add_btn.clicked.connect(self._add_entry)
        form_row.addWidget(self.plate_input)
        form_row.addWidget(self.amount_input)
        form_row.addWidget(add_btn)
        layout.addLayout(form_row)

        self.conn_label = QLabel()
        self.conn_label.setObjectName("ConnLabel")
        layout.addWidget(self.conn_label)

        self.refresh()

    def _add_entry(self):
        plate = self.plate_input.text().strip()
        amount = self.amount_input.text().strip()
        if not plate:
            QMessageBox.warning(self, "Missing plate", "Please enter a plate number before adding.")
            return
        self.mongo.add_to_watchlist(plate, amount)
        self.plate_input.clear()
        self.amount_input.clear()
        self.refresh()

    def _delete_entry(self, plate_input):
        plate = plate_input.strip()
        self.mongo.delete_from_watchlist(plate)
        self.refresh()

    def refresh(self):
        records = self.mongo.get_watchlist(CONFIG.database.watch_list)
        self.table.setRowCount(len(records))
        for row, rec in enumerate(records):
            date_added = rec.get("date_added", "")
            date_str = date_added.strftime("%Y-%m-%d %H:%M") if hasattr(date_added, "strftime") else str(date_added)
            self.table.setItem(row, 0, QTableWidgetItem(rec.get("plate", "")))
            self.table.setItem(row, 1, QTableWidgetItem(rec.get("amount", "")))
            self.table.setItem(row, 2, QTableWidgetItem(date_str))
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("color: red; font-weight: bold;") 
            delete_btn.clicked.connect(lambda checked, p = rec.get("plate", ""): self._delete_entry(p))
            self.table.setCellWidget(row, 3, delete_btn)
            self.table.setRowHeight(row, 35) 

        state = "MongoDB: Connected" if getattr(self.mongo, "connected", False) else "MongoDB: Offline (using mock data)"
        self.conn_label.setText(state)
        self._apply_filter(self.search_input.text())

    def _apply_filter(self, text):
        query = text.strip().upper()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            plate = item.text().upper() if item else ""
            self.table.setRowHidden(row, bool(query) and query not in plate)