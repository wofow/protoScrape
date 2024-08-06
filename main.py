import os
import requests
from bs4 import BeautifulSoup
import hashlib
from collections import deque
from urllib.parse import urljoin, urlparse


def fetch_and_save_page(url, base_dir, queue, visited):
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text

        # Parse the HTML content
        soup = BeautifulSoup(content, 'html.parser')
        title = soup.title.string if soup.title else hashlib.md5(url.encode()).hexdigest()

        # Create a directory for the page
        page_dir = os.path.join(base_dir, title)
        os.makedirs(page_dir, exist_ok=True)

        # Save the HTML content
        html_path = os.path.join(page_dir, 'content.html')
        with open(html_path, 'w', encoding='utf-8') as file:
            file.write(content)

        # Save other relevant data (e.g., images, text)
        images = soup.find_all('img')
        for i, img in enumerate(images):
            img_url = img.get('src')
            if img_url:
                try:
                    img_data = requests.get(urljoin(url, img_url)).content
                    img_name = os.path.join(page_dir, f'image_{i}.jpg')
                    with open(img_name, 'wb') as img_file:
                        img_file.write(img_data)
                except Exception as e:
                    print(f"Could not save image {img_url}: {e}")

        # Find all links on the page and add
