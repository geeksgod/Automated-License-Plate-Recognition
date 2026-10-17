# Bowser Watch — Drive-Off Prevention

## Overview
Bowser Watch is a desktop application designed to prevent drive-offs at fuel stations by monitoring vehicle license plates and managing alerts. The application utilizes a MongoDB database for data storage and employs a user-friendly interface built with PyQt6.

## Project Structure
```
bowser-watch
├── entry.py
├── process
│   ├── __init__.py
│   └── bowser_watch_worker.py
├── ui
│   ├── __init__.py
│   ├── style.qss
│   ├── pumpcontrollpanel.py
│   ├── sidemenu.py
│   ├── watchlist.py
│   ├── fuelingrecord.py
│   └── reportpolice.py
├── watcher
│   ├── __init__.py
│   └── utils
│       ├── __init__.py
│       └── db.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

### Prerequisites
- Python 3.6 or higher
- MongoDB server

### Steps to Set Up the Project

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd bowser-watch
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   Install the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up MongoDB**
   Ensure that your MongoDB server is running. You may need to create a database and configure the connection settings in the `db.py` file located in the `watcher/utils` directory.

5. **Run the Application**
   Execute the main application file:
   ```bash
   python entry.py
   ```

## Usage
- Upon launching the application, you will see the main interface with options to control pumps, view the watchlist, and log fueling records.
- Use the sidebar to navigate between different panels.
- The application will monitor license plates and trigger alerts as necessary.

## File Descriptions

- `entry.py`: The main entry point of the application. Initializes the application and sets up the main window.
- `process/bowser_watch_worker.py`: Contains the `BowserWatchWorker` class that handles background tasks related to license plate detection and alert management.
- `ui/pumpcontrollpanel.py`: Defines the `PumpControlPanel` class for managing pump controls and displaying alerts.
- `ui/sidemenu.py`: Implements the sidebar menu for navigation between different application panels.
- `ui/watchlist.py`: Contains the `WatchlistPanel` class for displaying and managing the list of monitored license plates.
- `ui/fuelingrecord.py`: Implements the `FuelingLogPanel` class for logging fueling records and reporting incidents.
- `ui/reportpolice.py`: Defines the `ReportPoliceDialog` class for reporting incidents to the authorities.
- `watcher/utils/db.py`: Contains the `MongoDBManager` class for managing database connections and operations.
- `requirements.txt`: Lists the required Python packages for the project.
- `style.qss`: Contains the stylesheet for the application's UI.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.