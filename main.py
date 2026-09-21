"""
Forecourt Security Dashboard — Drive-Off Prevention Demo
==========================================================
Single-pump (Pump #1) ALPR / Watchlist monitoring dashboard.

Stack:
    - PyQt6 for the GUI
    - OpenCV (cv2) for the video feed (webcam / local mp4, QTimer-driven)
    - pymongo for MongoDB access (watchlist + fueling_logs collections)

Requirements:
    pip install PyQt6 opencv-python pymongo numpy

Run:
    python main.py

Design notes:
    - No real ALPR engine is wired up. Detection is simulated via the two
      "Demo Simulator" buttons, which feed a plate string through the same
      watchlist-check / pump-lock / logging pipeline a real detector would.
    - If MongoDB isn't reachable, MongoDBManager transparently falls back to
      in-memory mock data so the demo still runs end-to-end.
    - If no webcam/video file opens, the video panel falls back to a
      synthetic animated test pattern so the GUI still has a live feed.
    - Navigation: sections (Pump Control / Watchlist / Fueling Records /
      Demo Simulator) live behind a left-hand menu and are shown one at a
      time in a QStackedWidget. The live video feed is always visible.
    - Fueling records are rendered as cards (not table rows). Each card has
      an "Add to Watchlist" button (auto-adds that plate/log to the
      watchlist) and a "Report to Police" button that opens a confirmation
      dialog showing the vehicle details + a footage snapshot. Confirming
      simulates a submission to NSW Police (no real network call is made).
    - Both the Watchlist and Fueling Records sections have a rego search box.
"""

import sys
import random
import string
from datetime import datetime

import cv2
import numpy as np

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QHeaderView, QFrame, QMessageBox, QAbstractItemView,
    QScrollArea, QListWidget, QListWidgetItem, QStackedWidget, QDialog,
    QDialogButtonBox,QInputDialog
)

from config import CONFIG

from watcher.utils.db import MongoDBManager


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "forecourt_security"
VIDEO_SOURCE = "test1.mp4"  # webcam index, or a path to a local .mp4 sample file
PUMP_ID = "Pump #1"


# ---------------------------------------------------------------------------
# Dark theme stylesheet
# ---------------------------------------------------------------------------
DARK_QSS = """
QMainWindow { background-color: #14161c; }
QWidget {
    background-color: #14161c;
    color: #e6e8ec;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QFrame#Card, QFrame#VideoPanel {
    background-color: #1c1f27;
    border: 1px solid #2b303b;
    border-radius: 10px;
}
QLabel#SectionTitle {
    color: #8a93a6;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    padding-bottom: 4px;
    background: transparent;
}
QLabel#VideoLabel {
    background-color: #05060a;
    border-radius: 6px;
    border: 1px solid #2b303b;
}
QLabel#PlateHud {
    background-color: #0f1218;
    border: 1px solid #2b303b;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    font-weight: 600;
    color: #39ff88;
}
QLabel#AlertBanner {
    background-color: #8b0000;
    color: white;
    font-size: 18px;
    font-weight: 800;
    padding: 10px;
    border-radius: 6px;
    letter-spacing: 1px;
}
QLabel#PumpName {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    background: transparent;
}
QLabel#StatusBadgeOk {
    background-color: #0d3d1f;
    color: #39ff88;
    border: 2px solid #39ff88;
    border-radius: 8px;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 1px;
}
QLabel#StatusBadgeBlocked {
    background-color: #4d0000;
    color: #ff5252;
    border: 2px solid #ff1744;
    border-radius: 8px;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 1px;
}
QLabel#ConnLabel {
    color: #6b7280;
    font-size: 11px;
    font-style: italic;
    background: transparent;
}
QPushButton {
    background-color: #262b36;
    color: #e6e8ec;
    border: 1px solid #363c4a;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #313746; }
QPushButton:pressed { background-color: #1c2028; }
QPushButton#ResetButton { background-color: #2a3a55; border: 1px solid #3f5c8a; }
QPushButton#ResetButton:hover { background-color: #35496b; }
QPushButton#AddButton { background-color: #1f4d2e; border: 1px solid #39ff88; color: #39ff88; }
QPushButton#AddButton:hover { background-color: #245a36; }
QPushButton#RefreshButton { background-color: #23262f; }
QPushButton#SafeButton { background-color: #1f4d2e; border: 1px solid #39ff88; color: #39ff88; }
QPushButton#SafeButton:hover { background-color: #245a36; }
QPushButton#FlaggedButton { background-color: #5a0d0d; border: 1px solid #ff1744; color: #ff8080; }
QPushButton#FlaggedButton:hover { background-color: #6e1212; }
QLineEdit {
    background-color: #0f1218;
    border: 1px solid #2b303b;
    border-radius: 6px;
    padding: 6px 8px;
    color: #e6e8ec;
}
QLineEdit:focus { border: 1px solid #39ff88; }
QTableWidget {
    background-color: #0f1218;
    alternate-background-color: #14161c;
    gridline-color: #2b303b;
    border: 1px solid #2b303b;
    border-radius: 6px;
    selection-background-color: #2a3a55;
}
QHeaderView::section {
    background-color: #1c1f27;
    color: #8a93a6;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #2b303b;
    font-weight: 700;
}
QTableWidget::item { padding: 4px; }
QScrollBar:vertical { background: #14161c; width: 10px; }
QScrollBar::handle:vertical { background: #363c4a; border-radius: 5px; }

/* --- Sidebar navigation menu --- */
QListWidget#SidebarMenu {
    background-color: #1c1f27;
    border: 1px solid #2b303b;
    border-radius: 10px;
    padding: 8px;
    outline: none;
}
QListWidget#SidebarMenu::item {
    padding: 12px 14px;
    border-radius: 8px;
    color: #8a93a6;
    font-weight: 600;
    margin-bottom: 4px;
}
QListWidget#SidebarMenu::item:selected {
    background-color: #1f4d2e;
    color: #39ff88;
}
QListWidget#SidebarMenu::item:hover:!selected {
    background-color: #262b36;
    color: #e6e8ec;
}

/* --- Fueling record cards --- */
QFrame#RecordCard {
    background-color: #1c1f27;
    border: 1px solid #2b303b;
    border-radius: 10px;
}
QFrame#RecordCard[flagged="true"] { border: 1px solid #ff1744; }
QLabel#CardRego {
    font-size: 16px;
    font-weight: 800;
    color: #ffffff;
    background: transparent;
}
QLabel#CardMeta {
    color: #8a93a6;
    font-size: 12px;
    background: transparent;
}
QLabel#CardStatusOk {
    background-color: #0d3d1f;
    color: #39ff88;
    border-radius: 5px;
    padding: 3px 10px;
    font-weight: 700;
    font-size: 11px;
}
QLabel#CardStatusBlocked {
    background-color: #4d0000;
    color: #ff5252;
    border-radius: 5px;
    padding: 3px 10px;
    font-weight: 700;
    font-size: 11px;
}
QPushButton#WatchBtn {
    background-color: #2a3a55;
    border: 1px solid #3f5c8a;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton#WatchBtn:hover { background-color: #35496b; }
QPushButton#WatchBtn:disabled {
    background-color: #1c1f27;
    color: #565d6b;
    border: 1px solid #2b303b;
}
QPushButton#PoliceBtn {
    background-color: #5a0d0d;
    border: 1px solid #ff1744;
    color: #ff8080;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton#PoliceBtn:hover { background-color: #6e1212; }

/* --- Report-to-police dialog --- */
QLabel#DialogTitle {
    font-size: 17px;
    font-weight: 800;
    color: #ff5252;
    background: transparent;
}
QLabel#FootageLabel {
    background-color: #05060a;
    border: 1px solid #2b303b;
    border-radius: 6px;
    color: #565d6b;
}
QLabel#SuccessBanner {
    background-color: #0d3d1f;
    color: #39ff88;
    border: 1px solid #39ff88;
    border-radius: 6px;
    padding: 10px;
    font-weight: 700;
}
"""


# ---------------------------------------------------------------------------
# Section 1: Live video feed panel
# ---------------------------------------------------------------------------
class VideoPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VideoPanel")
        self._last_pixmap = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("LIVE FEED — Forecourt Camera 1")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.alert_banner = QLabel("SECURITY ALERT: WATCHLIST DETECTED")
        self.alert_banner.setObjectName("AlertBanner")
        self.alert_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alert_banner.hide()
        layout.addWidget(self.alert_banner)

        self.video_label = QLabel()
        self.video_label.setObjectName("VideoLabel")
        self.video_label.setMinimumSize(640, 320)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.video_label, stretch=1)

        hud_row = QHBoxLayout()
        self.plate_hud = QLabel("Detected Rego: -- | Confidence: --")
        self.plate_hud.setObjectName("PlateHud")
        hud_row.addWidget(self.plate_hud)
        hud_row.addStretch()
        layout.addLayout(hud_row)

        self._flash_state = False
        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._toggle_flash)

    def update_frame(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            max(self.video_label.width(), 1), max(self.video_label.height(), 1),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self._last_pixmap = pix
        self.video_label.setPixmap(pix)

    def get_current_pixmap(self):
        """Returns the most recently rendered video frame, for use as a
        'footage' snapshot elsewhere in the UI (e.g. the police report
        dialog). May be None if no frame has been rendered yet."""
        return self._last_pixmap

    def set_plate_hud(self, rego: str, confidence):
        self.plate_hud.setText(f"Detected Rego: {rego} | Confidence: {confidence}%")

    def set_alert(self, active: bool):
        if active:
            self.alert_banner.show()
            if not self._flash_timer.isActive():
                self._flash_timer.start(450)
        else:
            self._flash_timer.stop()
            self.alert_banner.hide()
            self.alert_banner.setStyleSheet("")

    def _toggle_flash(self):
        self._flash_state = not self._flash_state
        color = "#ff1744" if self._flash_state else "#8b0000"
        self.alert_banner.setStyleSheet(f"background-color:{color}; color:white;")


# ---------------------------------------------------------------------------
# Section 2: Pump control panel
# ---------------------------------------------------------------------------
class PumpControlPanel(QFrame):
    reset_requested = pyqtSignal()

    def __init__(self, pump_id: str = PUMP_ID, parent=None):
        super().__init__(parent)
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


# ---------------------------------------------------------------------------
# Section 3: Watchlist management panel
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Report-to-police confirmation dialog
# ---------------------------------------------------------------------------
class ReportPoliceDialog(QDialog):
    """Confirmation pop-up shown when the user clicks 'Report to Police' on
    a fueling record card. Displays the vehicle info + a footage snapshot,
    and on confirmation *simulates* a successful submission to NSW Police —
    no real network call is made."""

    def __init__(self, record: dict, footage_pixmap: QPixmap = None, parent=None):
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("Report to NSW Police")
        self.setMinimumWidth(460)
        if parent is not None:
            self.setStyleSheet(parent.styleSheet())

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        title = QLabel("⚠ Confirm Report to NSW Police")
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
        if footage_pixmap is not None and not footage_pixmap.isNull():
            self.footage_label.setPixmap(
                footage_pixmap.scaled(
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
        form.addRow("Plate Rego:", QLabel(record.get("plate", "—")))
        form.addRow("Pump:", QLabel(str(record.get("pump", PUMP_ID))))
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


# ---------------------------------------------------------------------------
# Fueling record card
# ---------------------------------------------------------------------------
class FuelingRecordCard(QFrame):
    add_to_watchlist_requested = pyqtSignal(dict)
    report_police_requested = pyqtSignal(dict)

    def __init__(self, record: dict, already_watchlisted: bool = False, parent=None):
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
        btn_row.addWidget(self.watch_btn)

        police_btn = QPushButton("Report to Police")
        police_btn.setObjectName("PoliceBtn")
        police_btn.clicked.connect(lambda: self.report_police_requested.emit(self.record))
        btn_row.addWidget(police_btn)

        btn_row.addStretch()
        outer.addLayout(btn_row)

        self.style().unpolish(self)
        self.style().polish(self)

    def _on_add_to_watchlist(self):
        self.add_to_watchlist_requested.emit(self.record)
        self.watch_btn.setText("✓ Added to Watchlist")
        self.watch_btn.setEnabled(False)


# ---------------------------------------------------------------------------
# Section 4: Today's fueling records panel (card view)
# ---------------------------------------------------------------------------
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
        self.search_input.setPlaceholderText("Search by rego…")
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
            rego = card.record.get("plate", "").upper()
            card.setVisible((query in rego) if query else True)



# ---------------------------------------------------------------------------
# Sidebar navigation menu
# ---------------------------------------------------------------------------
class SidebarMenu(QListWidget):
    SECTIONS = ["Pump Control", "Watchlist Management", "Fueling Records"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarMenu")
        self.setFixedWidth(220)
        for name in self.SECTIONS:
            QListWidgetItem(name, self)
        self.setCurrentRow(0)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forecourt Security Dashboard — Drive-Off Prevention")
        self.resize(1440, 900)
        self.setStyleSheet(DARK_QSS)

        self.mongo = MongoDBManager()

        # --- Video capture setup (webcam / file, with synthetic fallback) ---
        self.cap = cv2.VideoCapture(VIDEO_SOURCE)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = None
        self._synthetic_frame_counter = 0

        # --- Widgets ---
        self.pump_panel = PumpControlPanel()
        self.watchlist_panel = WatchlistPanel(self.mongo)
        self.fueling_panel = FuelingLogPanel(self.mongo)
        self.sidebar = SidebarMenu()

        self.pump_panel.reset_requested.connect(self._on_manual_reset)
        self.fueling_panel.add_to_watchlist_requested.connect(self._on_add_to_watchlist)
        self.fueling_panel.report_police_requested.connect(self._on_report_police)
        

        self._build_layout()

        # --- Video timer (~30fps) ---
        self.video_timer = QTimer(self)
        self.video_timer.start(33)

    def _build_layout(self):
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # Left: navigation menu
        root.addWidget(self.sidebar)

        # Right: video feed (always visible) + the section chosen from the menu
        content_col = QVBoxLayout()
        content_col.setSpacing(16)

        self.stacked = QStackedWidget()
        self.stacked.addWidget(self._wrap_top(self.pump_panel))
        self.stacked.addWidget(self.watchlist_panel)
        self.stacked.addWidget(self.fueling_panel)
        content_col.addWidget(self.stacked, stretch=3)

        content_wrap = QWidget()
        content_wrap.setLayout(content_col)
        root.addWidget(content_wrap, stretch=1)

        self.setCentralWidget(central)

        self.sidebar.currentRowChanged.connect(self.stacked.setCurrentIndex)

    @staticmethod
    def _wrap_top(widget):
        """Wraps a compact panel in a container that pins it to the top of
        the stacked page instead of stretching it to fill the whole area."""
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(widget)
        v.addStretch(1)
        return wrap



   

    # ---- Detection / simulation pipeline ----
    def _simulate_plate(self, rego: str):
        confidence = random.randint(88, 99)
        self.video_panel.set_plate_hud(rego, confidence)

        watch_entry = self.mongo.check_watchlist(rego)
        if watch_entry:
            self._trigger_alert()
            status = "Blocked"
        else:
            self._clear_alert()
            status = "Authorized"

        litres = round(random.uniform(15, 60), 2)
        self.mongo.log_fueling(rego, PUMP_ID, litres, status)
        self.fueling_panel.refresh()

    def _trigger_alert(self):
        self.pump_panel.set_status(ok=False)

    def _clear_alert(self):
        self.pump_panel.set_status(ok=True)

    def _on_manual_reset(self):
        self._clear_alert()

    # ---- Card actions: watchlist / police report ----
    def _on_add_to_watchlist(self, record: dict):
        rego = record.get("plate", "").strip()
        if not rego:
            return
        default_text = f"Auto-added from fueling log ({record.get('status', 'Unknown')})"
        reason, ok = QInputDialog.getText(
            self, 
            "Add to Watchlist", 
            f"Enter reason for {rego}:", 
            text=default_text
        )
        if ok:
            if not reason.strip():
                reason = "No reason provided"
            self.mongo.add_to_watchlist(rego, reason)
            self.watchlist_panel.refresh()
            QMessageBox.information(self, "Added to Watchlist", f"{rego} has been added to the watchlist.")

    def _on_report_police(self, record: dict):
        footage = self.video_panel.get_current_pixmap()
        dialog = ReportPoliceDialog(record, footage_pixmap=footage, parent=self)
        dialog.exec()

    def closeEvent(self, event):
        if self.cap is not None:
            self.cap.release()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()