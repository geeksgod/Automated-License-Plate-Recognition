from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QHeaderView, QFrame, QMessageBox, QAbstractItemView,
    QScrollArea, QListWidget, QListWidgetItem, QStackedWidget, QDialog,
    QDialogButtonBox,QInputDialog
)

class SidebarMenu(QListWidget):
    SECTIONS = ["Pump Control", "Watchlist Management", "Fueling Records"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarMenu")
        self.setFixedWidth(220)
        for name in self.SECTIONS:
            QListWidgetItem(name, self)
        self.setCurrentRow(0)