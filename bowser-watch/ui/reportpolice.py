from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox

class ReportPoliceDialog(QDialog):
    def __init__(self, record: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Report Incident to Police")
        self.setFixedSize(400, 300)

        self.record = record
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.plate_label = QLabel(f"License Plate: {self.record.get('plate', 'Unknown')}")
        layout.addWidget(self.plate_label)

        self.details_label = QLabel("Incident Details:")
        layout.addWidget(self.details_label)

        self.details_input = QLineEdit()
        layout.addWidget(self.details_input)

        self.submit_button = QPushButton("Submit Report")
        self.submit_button.clicked.connect(self.submit_report)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def submit_report(self):
        details = self.details_input.text().strip()
        if not details:
            QMessageBox.warning(self, "Input Error", "Please provide incident details.")
            return

        # Here you would typically send the report to the authorities
        # For now, we will just show a message box
        QMessageBox.information(self, "Report Submitted", "Your report has been submitted successfully.")
        self.accept()  # Close the dialog after submission