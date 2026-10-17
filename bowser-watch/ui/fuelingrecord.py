from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

class FuelingLogPanel(QWidget):
    report_police_requested = pyqtSignal(dict)
    add_to_watchlist_requested = pyqtSignal(dict)

    def __init__(self, mongo):
        super().__init__()
        self.mongo = mongo
        self.setWindowTitle("Fueling Log")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()

        self.plate_input = QLineEdit(self)
        self.plate_input.setPlaceholderText("Enter vehicle license plate")
        layout.addWidget(self.plate_input)

        self.log_button = QPushButton("Log Fueling Record", self)
        self.log_button.clicked.connect(self._log_fueling_record)
        layout.addWidget(self.log_button)

        self.report_button = QPushButton("Report Police", self)
        self.report_button.clicked.connect(self._report_police)
        layout.addWidget(self.report_button)

        self.setLayout(layout)

    def _log_fueling_record(self):
        plate = self.plate_input.text().strip()
        if not plate:
            QMessageBox.warning(self, "Input Error", "Please enter a valid license plate.")
            return
        
        # Log the fueling record in the database
        self.mongo.log_fueling_record(plate)
        QMessageBox.information(self, "Success", f"Fueling record for {plate} logged successfully.")
        self.plate_input.clear()

    def _report_police(self):
        plate = self.plate_input.text().strip()
        if not plate:
            QMessageBox.warning(self, "Input Error", "Please enter a valid license plate.")
            return
        
        # Emit signal to report police
        self.report_police_requested.emit({"plate": plate})
        QMessageBox.information(self, "Reported", f"Police have been notified about {plate}.")
        self.plate_input.clear()