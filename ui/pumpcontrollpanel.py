from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QHeaderView, QFrame, QMessageBox, QAbstractItemView,
    QScrollArea, QListWidget, QListWidgetItem, QStackedWidget, QDialog,
    QDialogButtonBox,QInputDialog
)

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from ui.uicomponent.fuelcard import FuelingRecordCard

from config import CONFIG

class PumpControlPanel(QFrame):
    reset_requested = pyqtSignal()

    def __init__(self, mongo, pump_id: str = "Pump 1", parent=None):

        super().__init__(parent)
        self.mongo = mongo
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("PUMP CONTROL")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        pump_name = QLabel(pump_id)
        pump_name.setObjectName("PumpName")
        layout.addWidget(pump_name)

        self.status_badge = QLabel("STATUS: OK")
        self.status_badge.setObjectName("StatusBadgeOk")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setMinimumHeight(56)
        layout.addWidget(self.status_badge)

        self.reset_btn = QPushButton("Manual Reset / Unlock")
        self.reset_btn.setObjectName("ResetButton")
        self.reset_btn.clicked.connect(self.reset_requested.emit)
        layout.addWidget(self.reset_btn)

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

    def set_status(self, ok: bool):
        if ok:
            self.status_badge.setText("STATUS: OK")
            self.status_badge.setObjectName("StatusBadgeOk")
        else:
            self.status_badge.setText("STATUS: BLOCKED")
            self.status_badge.setObjectName("StatusBadgeBlocked")
        # re-polish so the new objectName picks up its QSS rule
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

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
                card = FuelingRecordCard(rec, already_watchlisted=already, show_button= False)
                self.cards_layout.addWidget(card)
                self._cards.append(card)
    
            self.cards_layout.addStretch()


