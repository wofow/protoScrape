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

        # Clean title to create a valid directory name
        clean_title = ''.join(e for e in title if e.isalnum() or e in (' ', '_', '-')).strip()

        # Create a directory for the page
        page_dir = os.path.join(base_dir, clean_title)
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

        # Save CSS files
        css_links = soup.find_all('link', rel='stylesheet')
        for i, link in enumerate(css_links):
            css_url = link.get('href')
            if css_url:
                try:
                    css_data = requests.get(urljoin(url, css_url)).text
                    css_name = os.path.join(page_dir, f'style_{i}.css')
                    with open(css_name, 'w', encoding='utf-8') as css_file:
                        css_file.write(css_data)
                except Exception as e:
                    print(f'Could not save CSS {css_url}: {e}')

        # Find all links on the page and add to the queue if not already visited
        links = soup.find_all('a', href=True)
        for link in links:
            link_url = urljoin(url, link['href'])
            if link_url not in visited and is_valid_url(link_url):
                queue.append(link_url)
                visited.add(link_url)

        print(f"Page '{clean_title}' saved successfully.")

    except Exception as e:
        print(f"Failed to fetch page {url}: {e}")


def is_valid_url(url):
    """Check if the URL is valid and belongs to the same domain."""
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and parsed.netloc != ''


def main():
    # Prompt the user for initial URLs to scrape
    initial_urls = input("Enter the initial URLs to scrape, separated by commas: ").split(',')

    # Strip any surrounding whitespace from each URL
    initial_urls = [url.strip() for url in initial_urls if url.strip()]

    if not initial_urls:
        print("No valid URLs provided. Exiting.")
        return

    # Define the base directory to store the pages
    base_dir = 'scraped_pages'
    os.makedirs(base_dir, exist_ok=True)

    # Create a queue for URLs to scrape and a set for visited URLs
    queue = deque(initial_urls)
    visited = set(initial_urls)

    # Fetch and save each page from the queue
    while queue:
        url = queue.popleft()
        fetch_and_save_page(url, base_dir, queue, visited)


if __name__ == '__main__':
    main()
