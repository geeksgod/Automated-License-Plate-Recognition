from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QHeaderView, QFrame, QMessageBox, QAbstractItemView,
    QScrollArea, QListWidget, QListWidgetItem, QStackedWidget, QDialog,
    QDialogButtonBox,QInputDialog,QSizePolicy
)
from PyQt6.QtGui import QPixmap,QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from ui.uicomponent.fuelcard import FuelingRecordCard

from config import CONFIG

import os
class PumpControlPanel(QFrame):
    reset_requested = pyqtSignal()

    def __init__(self, mongo, pump_id: str = "Pump 1", parent=None):

        super().__init__(parent)
        self.mongo = mongo
        self.setObjectName("Card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(450)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)        

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(8, 8, 8, 8)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 3. Mount container into scroll area, then add to your parent layout
        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area, 1)

        

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

    def check_watchlist(self,plate_queue):
        print(len(plate_queue))

    def refresh_queue(self, plate_queue):
        records = plate_queue.get_all()
        if not records:
            # Clear existing cards if queue is empty
            while self.cards_layout.count():
                item = self.cards_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()
            return

        # Cap to latest 500 records
        if len(records) > 500:
            records = records[:500]

        # plate_strings = [getattr(r, "plate", "") for r in records]
        # watchlist_hits = self.mongo.check_watchlist(plate_strings)
        # if watchlist_hits:
        #     print(watchlist_hits)
        # else:
        #     print("not hit")    

        # 2. Clean out old widgets cleanly
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        # 3. Add new cards with container as parent
        for rec in records:
            card = PlateCard(rec, parent=self.cards_container)
            self.cards_layout.addWidget(card)
            card.show()

        # 4. Force container and scroll area geometry refresh
        self.cards_container.adjustSize()
        self.cards_layout.update() 

    def show_alert(self, message: str):
        """Displays the alert section with a custom warning message."""
        self.alert_label.setText(message)
        self.alert_widget.setVisible(True)

    def hide_alert(self):
        """Hides the alert section when everything is normal."""
        self.alert_widget.setVisible(False)   

    
class PlateCard(QFrame):
    """Card widget representing a single plateInfo item."""

    def __init__(self, rec, parent=None):
        super().__init__(parent)
        self.setObjectName("PlateCard")
        self.setStyleSheet("""
            #PlateCard {
                background-color: #2b2b2b;
                border-radius: 8px;
                border: 1px solid #3d3d3d;
            }
            #PlateCard:hover {
                border: 1px solid #5a5a5a;
            }
            QLabel {
                color: #ffffff;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 12, 8)
        layout.setSpacing(12)

        # 1. Thumbnail
        img_label = QLabel()
        img_label.setFixedSize(70, 48)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setStyleSheet(
            "background-color: #1a1a1a; border-radius: 4px;"
        )

        image_path = getattr(rec, "image", None) or getattr(rec, "frame", "")
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                img_label.setPixmap(
                    pixmap.scaled(
                        70,
                        48,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            else:
                img_label.setText("Corrupt")
        else:
            img_label.setText("No Img")

        layout.addWidget(img_label)

        # 2. Text Details (Plate & Confidence)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Plate / Rego Label
        plate_label = QLabel(str(getattr(rec, "plate", "") or "UNKNOWN"))
        plate_font = QFont()
        plate_font.setPointSize(12)
        plate_font.setBold(True)
        plate_label.setFont(plate_font)
        info_layout.addWidget(plate_label)

        # Confidence Label
        conf = getattr(rec, "confidence", None)
        if isinstance(conf, (int, float)):
            conf_str = f"{conf * 100:.1f}%" if conf <= 1.0 else f"{conf:.1f}%"
        else:
            conf_str = "N/A"

        conf_label = QLabel(f"Confidence: {conf_str}")
        conf_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        info_layout.addWidget(conf_label)

        layout.addLayout(info_layout)
        layout.addStretch()


