from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QMessageBox
from watcher.utils.db import MongoDBManager

class WatchlistPanel(QWidget):
    def __init__(self, mongo: MongoDBManager):
        super().__init__()
        self.mongo = mongo
        self.setLayout(QVBoxLayout())
        
        self.label = QLabel("Watchlist")
        self.layout().addWidget(self.label)

        self.watchlist_widget = QListWidget()
        self.layout().addWidget(self.watchlist_widget)

        self.refresh_button = QPushButton("Refresh Watchlist")
        self.refresh_button.clicked.connect(self.refresh)
        self.layout().addWidget(self.refresh_button)

        self.populate_watchlist()

    def populate_watchlist(self):
        self.watchlist_widget.clear()
        watchlist_items = self.mongo.get_watchlist()  # Assuming this method exists
        for item in watchlist_items:
            self.watchlist_widget.addItem(item)

    def refresh(self):
        self.populate_watchlist()
        QMessageBox.information(self, "Refreshed", "Watchlist has been refreshed.")