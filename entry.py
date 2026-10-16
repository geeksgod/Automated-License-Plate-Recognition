from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QMessageBox, QStackedWidget, QInputDialog
)
import sys
from watcher.utils.db import MongoDBManager

from ui.pumpcontrollpanel import PumpControlPanel
from ui.sidemenu import SidebarMenu
from ui.watchlist import WatchlistPanel
from ui.fuelingrecord import FuelingLogPanel
from ui.reportpolice import ReportPoliceDialog
from process import BowserWatchWorker

class MainWindow(QMainWindow):
    def __init__(self):
            super().__init__()
            self.setWindowTitle("BowserWatch — Drive-Off Prevention")
            self.resize(1440, 900)
            with open("ui/style.qss", "r") as f:
                self.setStyleSheet(f.read())
            self.mongo = MongoDBManager()

            self.pump_panel = PumpControlPanel(mongo= self.mongo)
            self.sidebar = SidebarMenu()
            self.watch_list = WatchlistPanel(mongo = self.mongo)
            self.fuelingrecord = FuelingLogPanel(mongo= self.mongo )

            self.fuelingrecord.report_police_requested.connect(self._on_report_police)
            self.fuelingrecord.add_to_watchlist_requested.connect(self._on_add_to_watchlist)
            self.pump_panel.is_resolved.connect(self.watch_list.refresh)

            self.worker = BowserWatchWorker(mongo=self.mongo)
            self.worker.plate_detected.connect(self.pump_panel.refresh_queue)
            self.worker.alert_triggered.connect(self.pump_panel.add_alert)
            self.worker.start()
            self._build_layout()
           
           
    def _build_layout(self):
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)
        root.addWidget(self.sidebar)

        content_col = QVBoxLayout()

        self.stacked = QStackedWidget()
        self.stacked.addWidget(self._wrap_top(self.pump_panel)) 
        self.stacked.addWidget(self.watch_list)
        self.stacked.addWidget(self.fuelingrecord)
        content_col.addWidget(self.stacked, stretch=3)
        
        content_wrap = QWidget()
        content_wrap.setLayout(content_col)
        root.addWidget(content_wrap, stretch=1)
        self.setCentralWidget(central)

        self.sidebar.currentRowChanged.connect(self.stacked.setCurrentIndex)

    @staticmethod
    def _wrap_top(widget):
       
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(widget)
        v.addStretch(1)
        return wrap

    

    def _on_add_to_watchlist(self, record: dict):
        plate = record.get("plate", "").strip()
        if not plate:
            return
        default_text = f"Auto-added from fueling log ({record.get('status', 'Unknown')})"
        amount, ok = QInputDialog.getText(
            self, 
            "Add to Watchlist", 
            f"Enter cost of fuel and liters {plate}:", 
            text=default_text
        )
        if ok:
            if not amount.strip():
                amount = "No amount provided"
            self.mongo.add_to_watchlist(plate, amount)
            self.watch_list.refresh()
            QMessageBox.information(self, "Added to Watchlist", f"{plate} has been added to the watchlist.")
        else:
            pass

    def _on_report_police(self, record: dict):
        dialog = ReportPoliceDialog(record, parent=self)
        dialog.exec()

    def closeEvent(self, event):
        self.mongo.close()
        super().closeEvent(event)
    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
