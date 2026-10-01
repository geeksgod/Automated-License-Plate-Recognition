
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QHeaderView, QFrame, QMessageBox, QAbstractItemView,
    QScrollArea, QListWidget, QListWidgetItem, QStackedWidget, QDialog,
    QDialogButtonBox,QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from watcher.utils.db import MongoDBManager
from ui.uicomponent.fuelcard import FuelingRecordCard


from config import CONFIG
class FuelingLogPanel(QFrame):
    add_to_watchlist_requested = pyqtSignal(dict)
    report_police_requested = pyqtSignal(dict)

    def __init__(self, mongo: MongoDBManager, parent=None):
        super().__init__(parent)
        self.mongo = mongo
        self.setObjectName("Card")
        self._cards = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        title = QLabel("TODAY'S FUELING RECORDS")
        title.setObjectName("SectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()
        refresh_btn = QPushButton("Refresh Logs")
        refresh_btn.setObjectName("RefreshButton")
        refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by plate…")
        self.search_input.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_input)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()
        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area, stretch=1)

        self.refresh()

    def refresh(self):
        records = self.mongo.get_todays_logs(CONFIG.database.all_plates)
        # clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        self._cards = []

        for rec in records:
            already = bool(self.mongo.get_todays_logs(rec.get("plate", "")))
            card = FuelingRecordCard(rec, already_watchlisted=already)
            card.add_to_watchlist_requested.connect(self.add_to_watchlist_requested.emit)
            card.report_police_requested.connect(self.report_police_requested.emit)
            self.cards_layout.addWidget(card)
            self._cards.append(card)

        self.cards_layout.addStretch()
        self._apply_filter(self.search_input.text())

    def _apply_filter(self, text):
        query = text.strip().upper()
        for card in self._cards:
            plate = card.record.get("plate", "").upper()
            card.setVisible((query in plate) if query else True)