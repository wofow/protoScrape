import requests
from bs4 import BeautifulSoup


class PreScan:
    def __init__(self, urls):
        self.urls = urls
        self.results = {}

    def scan_url(self, url):
        """Scan a single URL for available content."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check for available content types
            has_photos = bool(soup.find_all('img'))
            has_videos = bool(soup.find_all('video'))
            has_page_struct = True  # Assume page structure is always available

            options = []
            if has_photos:
                options.append("Photos")
            if has_videos:
                options.append("Videos")
            if has_page_struct:
                options.append("Page Structs")

            return options
        except Exception as e:
            print(f"Error scanning {url}: {e}")
            return []

    def run_scan(self):
        """Scan all URLs and store the results."""
        for url in self.urls:
            self.results[url] = self.scan_url(url)

        return self.results
