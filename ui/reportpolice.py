from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QHeaderView, QFrame, QMessageBox, QAbstractItemView,
    QScrollArea, QListWidget, QListWidgetItem, QStackedWidget, QDialog,
    QDialogButtonBox,QInputDialog
)

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from ui.uicomponent.fuelcard import FuelingRecordCard
from PyQt6.QtGui import QImage, QPixmap, QColor
import random, string
from config import CONFIG

class ReportPoliceDialog(QDialog):
    
    def __init__(self, record: dict, parent=None):
        super().__init__(parent)
        self.record = record
        self.footage_pixmap = QPixmap(record.get("image"))
        self.setWindowTitle("Report to NSW Police")
        self.setMinimumWidth(460)
        if parent is not None:
            self.setStyleSheet(parent.styleSheet())

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        title = QLabel("Confirm Report to NSW Police")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        warn = QLabel(
            "You are about to report this vehicle in connection with a "
            "suspected drive-off / watchlist incident. Please review the "
            "details below before submitting."
        )
        warn.setWordWrap(True)
        root.addWidget(warn)

        # Footage snapshot
        self.footage_label = QLabel()
        self.footage_label.setObjectName("FootageLabel")
        self.footage_label.setFixedHeight(220)
        self.footage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.footage_pixmap is not None and not self.footage_pixmap.isNull():
            self.footage_label.setPixmap(
                self.footage_pixmap.scaled(
                    420, 220, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            self.footage_label.setText("No footage snapshot available")
        root.addWidget(self.footage_label)

        # Vehicle info
        form = QFormLayout()
        form.setSpacing(6)
        ts = record.get("timestamp")
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts, "strftime") else str(ts)
        form.addRow("plate plate:", QLabel(record.get("plate", "—")))
        form.addRow("Pump:", QLabel(str(record.get("pump", "PUMP_ID"))))
        form.addRow("Litres Dispensed:", QLabel(str(record.get("litres", "—"))))
        form.addRow("Status:", QLabel(record.get("status", "—")))
        form.addRow("Timestamp:", QLabel(ts_str))
        root.addLayout(form)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        button_box = QDialogButtonBox()
        self.confirm_btn = QPushButton("Confirm & Submit to NSW Police")
        self.confirm_btn.setObjectName("PoliceBtn")
        self.confirm_btn.clicked.connect(self._submit)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_box.addButton(self.confirm_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(self.cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)
        root.addWidget(button_box)

    def _submit(self):
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setText("Submitting to NSW Police…")
        self.status_label.setText("Connecting to NSW Police reporting gateway (simulated)…")
        QTimer.singleShot(1200, self._on_submitted)

    def _on_submitted(self):
        reference = "NSW-" + "".join(random.choices(string.digits, k=8))
        self.record["police_reference"] = reference

        self.status_label.setObjectName("SuccessBanner")
        self.status_label.setText(
            f"✓ Report submitted successfully.\n"
            f"NSW Police reference: {reference}\n"
            f"(Simulated submission for demo purposes — no real report was sent.)"
        )
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        self.confirm_btn.hide()
        self.cancel_btn.setText("Close")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.accept)