import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QFileDialog, QComboBox, QMessageBox
)
from collections import deque
from ops.fetch import PageFetcher


class ScraperUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Scraper")
        self.setGeometry(100, 100, 600, 400)

        # Main widget and layout
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)

        # URL input
        self.url_label = QLabel("Enter URLs (comma-separated):")
        self.url_input = QLineEdit()
        self.layout.addWidget(self.url_label)
        self.layout.addWidget(self.url_input)

        # Output directory selection
        self.dir_label = QLabel("Output Directory: Not Selected")
        self.dir_button = QPushButton("Select Output Directory")
        self.dir_button.clicked.connect(self.select_directory)
        self.layout.addWidget(self.dir_label)
        self.layout.addWidget(self.dir_button)

        # Scraping options
        self.option_label = QLabel("Scraping Options:")
        self.option_dropdown = QComboBox()
        self.option_dropdown.addItems(["All", "Photos", "Videos", "Page Structs", "Photos and Videos"])
        self.layout.addWidget(self.option_label)
        self.layout.addWidget(self.option_dropdown)

        # Start scraping button
        self.start_button = QPushButton("Start Scraping")
        self.start_button.clicked.connect(self.start_scraping)
        self.layout.addWidget(self.start_button)

        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.layout.addWidget(self.log_area)

        # Set the central widget
        self.setCentralWidget(self.central_widget)

        # Variables
        self.output_dir = None

    def select_directory(self):
        """Open a file dialog to select the output directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir = directory
            self.dir_label.setText(f"Output Directory: {directory}")

    def start_scraping(self):
        """Start the scraping process."""
        urls = self.url_input.text().split(',')
        urls = [url.strip() for url in urls if url.strip()]

        if not urls:
            QMessageBox.warning(self, "Input Error", "Please enter valid URLs.")
            return

        if not self.output_dir:
            QMessageBox.warning(self, "Directory Error", "Please select an output directory.")
            return

        selected_option = self.option_dropdown.currentText()

        # Initialize PageFetcher and start scraping
        self.log_area.append("Starting scraping process...")
        try:
            queue = deque(urls)
            visited = set(urls)
            page_fetcher = PageFetcher(self.output_dir)

            while queue:
                url = queue.popleft()
                self.log_area.append(f"Scraping: {url}")
                page_fetcher.fetch_and_save_page(url, queue, visited)
                self.log_area.append(f"Finished: {url}")

            self.log_area.append("Scraping completed successfully!")
        except Exception as e:
            self.log_area.append(f"Error: {e}")
            QMessageBox.critical(self, "Scraping Error", f"An error occurred: {e}")


# Function to run the PyQt application
def run_ui():
    app = QApplication(sys.argv)
    window = ScraperUI()
    window.show()
    sys.exit(app.exec_())
