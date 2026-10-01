import sys
import time
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, 
    QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
)

class DetectorWorker(QThread):
    # Signal sending (plate_number, timestamp, confidence)
    plate_detected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True

    def run(self):
        """Simulate or run actual detection loop here."""
        while self.running:
            # Replace this block with your actual detector output
            time.sleep(1.5)  # Simulate detection interval
            detection = {
                "plate": "7XYZ890",
                "confidence": 0.97,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            self.plate_detected.emit(detection)

    def stop(self):
        self.running = False
        self.wait()


class PlateDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live License Plate Monitor")
        self.resize(500, 400)

        # Setup Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Plate Number", "Confidence"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.table)
        self.setCentralWidget(central_widget)

        # Start Detector Thread
        self.worker = DetectorWorker()
        self.worker.plate_detected.connect(self.add_plate_record)
        self.worker.start()

    def add_plate_record(self, record: dict):
        """Safely called on the main UI thread via signal."""
        row = 0  # Insert at top so newest is always visible
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(record["timestamp"]))
        self.table.setItem(row, 1, QTableWidgetItem(record["plate"]))
        self.table.setItem(row, 2, QTableWidgetItem(f"{record['confidence'] * 100:.1f}%"))

        # Optional: Cap max rows to prevent unbounded memory growth
        if self.table.rowCount() > 500:
            self.table.removeRow(self.table.rowCount() - 1)

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlateDashboard()
    window.show()
    sys.exit(app.exec())