from PyQt6.QtWidgets import (
    QListWidget, QListWidgetItem
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