import os
import requests
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import urljoin, urlsplit
import time
from ops.isValid import is_valid_url


def _get_extension(url, default='bin'):
    """Extract a file extension from a URL path, falling back to a default."""
    path = urlsplit(url).path
    _, ext = os.path.splitext(path)
    return ext.lstrip('.') or default


class PageFetcher:
    # scrape_mode: 'All', 'Photos', 'Videos', 'Page Structs', 'Photos and Videos'
    def __init__(self, base_dir, scrape_mode='All', max_depth=2, progress_callback=None):
        self.base_dir = base_dir
        self.scrape_mode = scrape_mode
        self.max_depth = max_depth
        self.progress_callback = progress_callback
        self._stop_flag = False
        os.makedirs(base_dir, exist_ok=True)

    def stop(self):
        self._stop_flag = True

    @property
    def is_stopped(self):
        return self._stop_flag

    def _log(self, message):
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)

    def fetch_and_save_page(self, url, queue, visited, depth=0):
        """Fetch a page and save its resources and HTML content locally."""
        if self._stop_flag or depth > self.max_depth:
            return
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            title = (soup.title.string if soup.title else None) or hashlib.md5(url.encode()).hexdigest()
            clean_title = ''.join(e for e in title if e.isalnum() or e in (' ', '_', '-')).strip()[:80]
            page_dir = os.path.join(self.base_dir, clean_title)
            os.makedirs(page_dir, exist_ok=True)

            if self.scrape_mode in ('All', 'Photos', 'Photos and Videos'):
                self._save_images(soup, page_dir, url)

            if self.scrape_mode in ('All', 'Videos', 'Photos and Videos'):
                self._save_videos(soup, page_dir, url)

            if self.scrape_mode in ('All', 'Page Structs'):
                self._save_css_and_js(soup, page_dir, url)

            self._update_links(soup, url, queue, visited, clean_title, depth)

            with open(os.path.join(page_dir, 'content.html'), 'w', encoding='utf-8') as f:
                f.write(str(soup))

            self._log(f"✔ Saved '{clean_title}'")

        except requests.exceptions.Timeout:
            self._log(f"✘ Timeout: {url}")
        except requests.exceptions.HTTPError as e:
            self._log(f"✘ HTTP {e.response.status_code}: {url}")
        except Exception as e:
            self._log(f"✘ Failed {url}: {e}")

    def _save_resource(self, resource_url, folder, prefix, file_extension, retries=3):
        for attempt in range(retries):
            try:
                data = requests.get(resource_url, timeout=10).content
                name = f"{prefix}_{hashlib.md5(resource_url.encode()).hexdigest()}.{file_extension}"
                with open(os.path.join(folder, name), 'wb') as f:
                    f.write(data)
                return name
            except Exception as e:
                self._log(f"  ↳ Attempt {attempt + 1} failed for {resource_url}: {e}")
                if attempt < retries - 1:
                    time.sleep(1)
        self._log(f"  ✘ Could not save {resource_url} after {retries} attempts")
        return None

    def _save_images(self, soup, page_dir, base_url):
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                full_url = urljoin(base_url, str(src))
                name = self._save_resource(full_url, page_dir, 'image', _get_extension(full_url, 'jpg'))
                if name:
                    img['src'] = name

    def _save_videos(self, soup, page_dir, base_url):
        for video in soup.find_all('video'):
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    full_url = urljoin(base_url, str(src))
                    name = self._save_resource(full_url, page_dir, 'video', _get_extension(full_url, 'mp4'))
                    if name:
                        source['src'] = name

    def _save_css_and_js(self, soup, page_dir, base_url):
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, str(href))
                name = self._save_resource(full_url, page_dir, 'style', 'css')
                if name:
                    link['href'] = name

        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                full_url = urljoin(base_url, str(src))
                name = self._save_resource(full_url, page_dir, 'script', 'js')
                if name:
                    script['src'] = name

    def _update_links(self, soup, url, queue, visited, clean_title, depth):
        """Enqueue unvisited same-domain links and rewrite hrefs to local paths."""
        for a in soup.find_all('a', href=True):
            link_url = urljoin(url, str(a['href']))
            if link_url not in visited and is_valid_url(link_url):
                if depth + 1 <= self.max_depth:
                    queue.append((link_url, depth + 1))
                visited.add(link_url)

            if urlsplit(link_url).netloc == urlsplit(url).netloc:
                local = os.path.join('..', clean_title, hashlib.md5(link_url.encode()).hexdigest() + '.html')
                a['href'] = local
