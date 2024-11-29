import os
import requests
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import urljoin, urlsplit
import time
from ops.isValid import is_valid_url


class PageFetcher:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def fetch_and_save_page(self, url, queue, visited):
        """Fetch a page and save its resources and HTML content locally."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.text

            # Parse the HTML content
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.title.string if soup.title else hashlib.md5(url.encode()).hexdigest()

            # Clean title to create a valid directory name
            clean_title = ''.join(e for e in title if e.isalnum() or e in (' ', '_', '-')).strip()
            page_dir = os.path.join(self.base_dir, clean_title)
            os.makedirs(page_dir, exist_ok=True)

            # Save page resources (images, CSS, JS, videos)
            self._save_resources(soup, page_dir, url)

            # Update links in the page
            self._update_links(soup, url, queue, visited, clean_title)

            # Save the modified HTML content
            html_path = os.path.join(page_dir, 'content.html')
            with open(html_path, 'w', encoding='utf-8') as file:
                file.write(str(soup))

            print(f"Page '{clean_title}' saved successfully")

        except Exception as e:
            print(f"Failed to fetch page {url}: {e}")

    def _save_resources(self, soup, page_dir, url):
        """Save images, CSS, JS, and video resources from the page."""
        def save_resource(resource_url, folder, prefix, file_extension, retries=3):
            resource_url = urljoin(url, resource_url)
            for attempt in range(retries):
                try:
                    resource_data = requests.get(resource_url).content
                    resource_name = f"{prefix}_{hashlib.md5(resource_url.encode()).hexdigest()}.{file_extension}"
                    resource_path = os.path.join(folder, resource_name)
                    with open(resource_path, 'wb') as resource_file:
                        resource_file.write(resource_data)
                    return resource_name
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed to save resource {resource_url}: {e}")
                    if attempt < retries - 1:
                        time.sleep(2)
            print(f"Could not save resource {resource_url} after {retries} attempts")
            return None

        # Save images
        for img in soup.find_all('img'):
            img_url = img.get('src')
            if img_url:
                extension = 'jpg' if not img_url.endswith('.gif') else 'gif'
                img_name = save_resource(img_url, page_dir, 'image', extension)
                if img_name:
                    img['src'] = img_name

        # Save CSS files
        for link in soup.find_all('link', rel='stylesheet'):
            css_url = link.get('href')
            if css_url:
                css_name = save_resource(css_url, page_dir, 'style', 'css')
                if css_name:
                    link['href'] = css_name

        # Save JS files
        for script in soup.find_all('script', src=True):
            js_url = script.get('src')
            if js_url:
                js_name = save_resource(js_url, page_dir, 'script', 'js')
                if js_name:
                    script['src'] = js_name

        # Save videos
        for video in soup.find_all('video'):
            for source in video.find_all('source'):
                video_url = source.get('src')
                if video_url:
                    video_name = save_resource(video_url, page_dir, 'video', 'mp4')
                    if video_name:
                        source['src'] = video_name

    def _update_links(self, soup, url, queue, visited, clean_title):
        """Update and queue links found on the page."""
        for a in soup.find_all('a', href=True):
            link_url = urljoin(url, a['href'])
            if link_url not in visited and is_valid_url(link_url):
                queue.append(link_url)
                visited.add(link_url)

            # Update href to local path if within same domain
            if urlsplit(link_url).netloc == urlsplit(url).netloc:
                a['href'] = os.path.join('..', clean_title, hashlib.md5(link_url.encode()).hexdigest() + '.html')
