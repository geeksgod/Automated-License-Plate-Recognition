from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QHeaderView, QFrame, QMessageBox, QAbstractItemView,
    QScrollArea, QListWidget, QListWidgetItem, QStackedWidget, QDialog,
    QDialogButtonBox,QInputDialog
)
import sys
from watcher.utils.db import MongoDBManager

from ui.pumpcontrollpanel import PumpControlPanel
from ui.sidemenu import SidebarMenu
from ui.watchlist import WatchlistPanel
from ui.fuelingrecord import FuelingLogPanel


class MainWindow(QMainWindow):
    def __init__(self):
            super().__init__()
            self.setWindowTitle("Forecourt Security Dashboard — Drive-Off Prevention")
            self.resize(1440, 900)
            with open("ui/style.qss", "r") as f:
                self.setStyleSheet(f.read())
            self.mongo = MongoDBManager()



            self.pump_panel = PumpControlPanel(mongo= self.mongo)
            self.sidebar = SidebarMenu()
            self.watch_list = WatchlistPanel(mongo = self.mongo)
            self.fuelingrecord = FuelingLogPanel(mongo= self.mongo )

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
        """Wraps a compact panel in a container that pins it to the top of
        the stacked page instead of stretching it to fill the whole area."""
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(widget)
        v.addStretch(1)
        return wrap
    



app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())