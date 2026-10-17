from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

class PumpControlPanel(QWidget):
    is_resolved = pyqtSignal()
    
    def __init__(self, mongo):
        super().__init__()
        self.mongo = mongo
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Pump Status: OK")
        layout.addWidget(self.status_label)
        
        self.alert_button = QPushButton("Trigger Alert")
        self.alert_button.clicked.connect(self.trigger_alert)
        layout.addWidget(self.alert_button)
        
        self.resolve_button = QPushButton("Resolve Alert")
        self.resolve_button.clicked.connect(self.resolve_alert)
        layout.addWidget(self.resolve_button)
        
        self.setLayout(layout)

    def trigger_alert(self):
        self.set_status(ok=False)
        QMessageBox.warning(self, "Alert", "An alert has been triggered!")

    def resolve_alert(self):
        self.set_status(ok=True)
        self.is_resolved.emit()
        QMessageBox.information(self, "Resolved", "The alert has been resolved.")

    def set_status(self, ok: bool):
        if ok:
            self.status_label.setText("Pump Status: OK")
        else:
            self.status_label.setText("Pump Status: ALERT")