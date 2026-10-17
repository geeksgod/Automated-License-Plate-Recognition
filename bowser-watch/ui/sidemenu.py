from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QLabel, QListWidget

class SidebarMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)
        self.layout = QVBoxLayout(self)

        self.title = QLabel("Bowser Watch")
        self.layout.addWidget(self.title)

        self.menu_items = QListWidget()
        self.menu_items.addItems(["Pump Control", "Watchlist", "Fueling Records", "Report Police"])
        self.layout.addWidget(self.menu_items)

        self.setLayout(self.layout)