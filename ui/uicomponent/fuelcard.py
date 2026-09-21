from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QHeaderView, QFrame, QMessageBox, QAbstractItemView,
    QScrollArea, QListWidget, QListWidgetItem, QStackedWidget, QDialog,
    QDialogButtonBox,QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal


class FuelingRecordCard(QFrame):
    add_to_watchlist_requested = pyqtSignal(dict)
    report_police_requested = pyqtSignal(dict)

    def __init__(self, record: dict, already_watchlisted: bool = False, PUMP_ID : str = "Pump 1", show_button = True,  parent=None):
        super().__init__(parent)
        self.record = record
        self.setObjectName("RecordCard")
        self.setProperty("flagged", "true" if record.get("status") == "Blocked" else "false")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)

        top_row = QHBoxLayout()
        rego_label = QLabel(record.get("plate", "—"))
        rego_label.setObjectName("CardRego")
        top_row.addWidget(rego_label)
        top_row.addStretch()

        status = record.get("status", "Unknown")
        status_label = QLabel(status.upper())
        status_label.setObjectName("CardStatusBlocked" if status == "Blocked" else "CardStatusOk")
        top_row.addWidget(status_label)
        outer.addLayout(top_row)

        ts = record.get("timestamp")
        ts_str = ts.strftime("%H:%M:%S") if hasattr(ts, "strftime") else str(ts)
        meta = QLabel(f"{ts_str}   •   {record.get('pump', PUMP_ID)}   •   {record.get('litres', '—')} L")
        meta.setObjectName("CardMeta")
        outer.addWidget(meta)

        btn_row = QHBoxLayout()
        self.watch_btn = QPushButton("✓ On Watchlist" if already_watchlisted else "+ Add to Watchlist")
        self.watch_btn.setObjectName("WatchBtn")
        self.watch_btn.setEnabled(not already_watchlisted)
        self.watch_btn.clicked.connect(self._on_add_to_watchlist)
        if show_button == True : btn_row.addWidget(self.watch_btn)

        police_btn = QPushButton("Report to Police")
        police_btn.setObjectName("PoliceBtn")
        police_btn.clicked.connect(lambda: self.report_police_requested.emit(self.record))
        if show_button == True : btn_row.addWidget(police_btn)

        btn_row.addStretch()
        outer.addLayout(btn_row)

        self.style().unpolish(self)
        self.style().polish(self)

    def _on_add_to_watchlist(self):
        self.add_to_watchlist_requested.emit(self.record)
        self.watch_btn.setText("✓ Added to Watchlist")
        self.watch_btn.setEnabled(False)