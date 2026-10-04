from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QPixmap,QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QSoundEffect

import os
class PumpControlPanel(QFrame):
    is_resolved = pyqtSignal()
    alert_triggered = pyqtSignal(dict)
    seen_alert_plates = set()  

    def __init__(self, mongo, pump_id: str = "Pump 1", parent=None):

        super().__init__(parent)
        self.mongo = mongo
        self.setObjectName("Card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(600)

        self.alert_sound = QSoundEffect(self)
        self.alert_sound.setSource(QUrl.fromLocalFile(str(Path("audio/alert.wav").resolve())))
        self.alert_sound.setLoopCount(QSoundEffect.Loop.Infinite.value)  # Continuous loop
        self.alert_sound.setVolume(0.8)

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

        self.alert_scroll_area = QScrollArea()
        self.alert_scroll_area.setWidgetResizable(True)
        self.alert_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.alert_scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.alert_container = QWidget()
        self.alert_layout = QVBoxLayout(self.alert_container)
        self.alert_layout.setContentsMargins(8, 8, 8, 8)
        self.alert_layout.setSpacing(8)
        self.alert_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.alert_scroll_area.setWidget(self.alert_container)
        layout.addWidget(self.alert_scroll_area, 1)

        

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

        
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        for rec in records:
            card = PlateCard(rec, parent=self.cards_container)
            self.cards_layout.addWidget(card)
            card.show()

        self.cards_container.adjustSize()
        self.cards_layout.update() 

    
    def add_alert(self, alert_data: dict):
        plate = alert_data.get("plate", "").strip().upper()
        if not plate:
            return

        # Deduplication check
        if plate in self.seen_alert_plates:
            return
        
        if self.alert_sound.isLoaded():
            self.alert_sound.play()
            # Stop sound automatically after 3000 ms (3 seconds)
            QTimer.singleShot(50000, self.alert_sound.stop)
        self.seen_alert_plates.add(plate)

        alert_card = QFrame()
        alert_card.setStyleSheet("""
            QFrame {
                background-color: #3b1111;
                border: 1px solid #ff4444;
                border-radius: 6px;
                padding: 4px;
            }
        """)

        card_layout = QVBoxLayout(alert_card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(4)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        plate_label = QLabel(f"<b>PLATE:</b> {plate}")
        plate_label.setStyleSheet("color: #ffffff; font-size: 14px; border: none;")

        btn_delete = QPushButton("Resolved")
        btn_delete.setFixedSize(100, 100)
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setToolTip("Dismiss alert")
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ff9999;
                font-weight: bold;
                border: 1px solid #772222;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff4444;
                color: #ffffff;
            }
        """)
        btn_snooze = QPushButton("Snooze")
        btn_snooze.setFixedSize(100, 100)

        btn_delete.clicked.connect(lambda: self.dismiss_alert(plate, alert_card))
        btn_snooze.clicked.connect(lambda: self.snooze_alert(plate, alert_card))

        header_row.addWidget(plate_label)
        header_row.addStretch()
        header_row.addWidget(btn_delete)
        header_row.addWidget(btn_snooze)
        reason = alert_data.get("data", {}).get("reason", "Watchlist Match")
        reason_label = QLabel(f"<b>Reason:</b> {reason}")
        reason_label.setStyleSheet("color: #ff9999; font-size: 12px; border: none;")

        card_layout.addLayout(header_row)
        card_layout.addWidget(reason_label)

        self.alert_layout.insertWidget(0, alert_card)

    def dismiss_alert(self, plate: str, card_widget: QFrame):
        """Removes the alert widget and frees up the plate for re-detection."""
        self.seen_alert_plates.discard(plate)
        self.alert_sound.stop()
        _ = self.mongo.delete_from_watchlist(plate)
        self.alert_layout.removeWidget(card_widget)
        self.is_resolved.emit()
        card_widget.deleteLater()

    def snooze_alert(self, plate: str, card_widget: QFrame):       
        self.alert_sound.stop()

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


