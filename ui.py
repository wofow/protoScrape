import sys
from collections import deque

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
    QComboBox, QMessageBox, QSpinBox
)

from ops.fetch import PageFetcher


# ---------------------------------------------------------------------------
# Background worker — keeps the UI responsive during scraping
# ---------------------------------------------------------------------------

class ScraperWorker(QThread):
    log_message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, urls, output_dir, scrape_mode, max_depth):
        super().__init__()
        self.urls = urls
        self.output_dir = output_dir
        self.scrape_mode = scrape_mode
        self.max_depth = max_depth
        self._fetcher = None

    def run(self):
        self._fetcher = PageFetcher(
            base_dir=self.output_dir,
            scrape_mode=self.scrape_mode,
            max_depth=self.max_depth,
            progress_callback=self.log_message.emit,
        )

        queue = deque((url, 0) for url in self.urls)
        visited = set(self.urls)

        while queue:
            if self._fetcher._stop_flag:
                self.log_message.emit("⏹ Scraping stopped by user.")
                break
            url, depth = queue.popleft()
            self.log_message.emit(f"→ Scraping (depth {depth}): {url}")
            self._fetcher.fetch_and_save_page(url, queue, visited, depth)

        self.finished.emit()

    def stop(self):
        if self._fetcher:
            self._fetcher.stop()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class ScraperUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("protoScrape")
        self.setGeometry(100, 100, 680, 520)

        self._worker = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)

        # --- URL input ---
        layout.addWidget(QLabel("URLs to scrape (comma-separated):"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com, https://other.com")
        layout.addWidget(self.url_input)

        # --- Output directory ---
        dir_row = QHBoxLayout()
        self.dir_label = QLabel("No output directory selected")
        self.dir_label.setWordWrap(True)
        dir_btn = QPushButton("Browse…")
        dir_btn.setFixedWidth(80)
        dir_btn.clicked.connect(self._select_directory)
        dir_row.addWidget(self.dir_label, stretch=1)
        dir_row.addWidget(dir_btn)
        layout.addLayout(dir_row)

        # --- Options row ---
        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("Scrape:"))
        self.option_dropdown = QComboBox()
        self.option_dropdown.addItems(["All", "Photos", "Videos", "Page Structs", "Photos and Videos"])
        options_row.addWidget(self.option_dropdown)
        options_row.addSpacing(20)
        options_row.addWidget(QLabel("Max depth:"))
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(0, 10)
        self.depth_spin.setValue(2)
        self.depth_spin.setToolTip(
            "0 = only the seed URLs\n"
            "1 = seed URLs + their direct links\n"
            "2+ = follow links recursively"
        )
        options_row.addWidget(self.depth_spin)
        options_row.addStretch()
        layout.addLayout(options_row)

        # --- Action buttons ---
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("▶  Start Scraping")
        self.start_btn.clicked.connect(self._start_scraping)
        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.clicked.connect(self._stop_scraping)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        layout.addLayout(btn_row)

        # --- Log area ---
        layout.addWidget(QLabel("Log:"))
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        self.output_dir = None

    def _select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir = directory
            self.dir_label.setText(f"Output: {directory}")

    def _start_scraping(self):
        urls = [u.strip() for u in self.url_input.text().split(',') if u.strip()]
        if not urls:
            QMessageBox.warning(self, "Input Error", "Please enter at least one URL.")
            return
        if not self.output_dir:
            QMessageBox.warning(self, "Directory Error", "Please select an output directory.")
            return

        self.log_area.clear()
        self.log_area.append("Starting scrape…\n")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self._worker = ScraperWorker(
            urls=urls,
            output_dir=self.output_dir,
            scrape_mode=self.option_dropdown.currentText(),
            max_depth=self.depth_spin.value(),
        )
        self._worker.log_message.connect(self.log_area.append)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _stop_scraping(self):
        if self._worker:
            self._worker.stop()
        self.stop_btn.setEnabled(False)

    def _on_finished(self):
        self.log_area.append("\n✔ Done.")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_ui():
    app = QApplication(sys.argv)
    window = ScraperUI()
    window.show()
    sys.exit(app.exec_())
