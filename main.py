import os
import requests
from bs4 import BeautifulSoup
import hashlib
from collections import deque
from urllib.parse import urljoin, urlparse, urlsplit


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

        # Function to save content and adjust links
        def save_resource(resource_url, folder, prefix, extension):
            resource_url = urljoin(url, resource_url)
            resource_data = requests.get(resource_url).content
            resource_name = f"{prefix}_{hashlib.md5(resource_url.encode()).hexdigest()}.{extension}"
            resource_path = os.path.join(folder, resource_name)
            with open(resource_path, 'wb') as resource_file:
                resource_file.write(resource_data)
            return resource_name

        # Update image sources
        for img in soup.find_all('img'):
            img_url = img.get('src')
            if img_url:
                try:
                    # Determine image extension
                    extension = 'jpg'
                    if img_url.endswith('.gif'):
                        extension = '.gif'
                    img_name = save_resource(img_url, page_dir, 'image', extension)
                    img['src'] = img_name
                except Exception as e:
                    print(f"could not save image {img_url}: {e}")

        # Update CSS links
        for link in soup.find_all('link', rel='stylesheet'):
            css_url = link.get('href')
            if css_url:
                try:
                    css_name = save_resource(css_url, page_dir, 'style', 'css')
                    link['href'] = css_name
                except Exception as e:
                    print(f"Could not save CSS {css_url}: {e}")

        # Update JS links
        for script in soup.find_all('script', src=True):
            js_url = script.get('src')
            if js_url:
                try:
                    js_name = save_resource(js_url, page_dir, 'script', 'js')
                    script['src'] = js_name
                except Exception as e:
                    print(f"Could not save JS {js_url}: {e}")

        # Update video sources
        for video in soup.find_all('video'):
            for source in video.find_all('source'):
                video_url = source.get('src')
                if video_url:
                    try:
                        video_name = save_resource(video_url, page_dir, 'video', 'mp4')
                        source['src'] = video_name
                    except Exception as e:
                        print(f"Could not save video {video_url}: {e}")

        # Update Links
        for a in soup.find_all('a', href=True):
            link_url = urljoin(url, a['href'])
            if link_url not in visited and is_valid_url(link_url):
                queue.append(link_url)
                visited.add(link_url)
            # Update href to local path if within same domain
            if urlsplit(link_url).netloc == urlsplit(url).netloc:
                a['href'] = os.path.join('..', clean_title, hashlib.md5(link_url.encode()).hexdigest() + '.html')

        # Save the HTML content
        html_path = os.path.join(page_dir, 'content.html')
        with open(html_path, 'w', encoding='utf-8') as file:
            file.write(str(soup))

        print(f"Page '{clean_title} saved successfully")

    except Exception as e:
        print(f"Failed to fetch page {url}: {e}")


def is_valid_url(url):
    """Check if URL is valid and belongs to same domain."""
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and parsed.netloc != ''


def main():
    # Prompt user for initial URLs to scrape
    initial_urls = input("Enter the initial URLs to scrape, separated by commas: ").split(',')

    # Strip any surrounding whitespace from each URL
    initial_urls = [url.strip() for url in initial_urls if url.strip()]

    if not initial_urls:
        print("No valid URLs provided. Exiting.")
        return

    # Define base directory to store pages
    base_dir = input("What would you like to name the main output folder? ")
    os.makedirs(base_dir, exist_ok=True)

    # Create a que for URLs to scrape and a set for visited URLs
    queue = deque(initial_urls)
    visited = set(initial_urls)

    # Fetch and save each page from queue
    while queue:
        url = queue.popleft()
        fetch_and_save_page(url, base_dir, queue, visited)


if __name__ == '__main__':
    main()
