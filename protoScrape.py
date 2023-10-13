import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


def extract_html_and_css(url):
    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract HTML content
        html_content = str(soup)

        # Extract CSS styles
        css_links = []
        css_content = ""
        for link in soup.find_all('link', rel='stylesheet'):
            css_url = link.get('href')
            # Create an absolute URL by joining with the base URL
            css_url = urljoin(url, css_url)
            css_response = requests.get(css_url)
            if css_response.status_code == 200:
                css_links.append(css_url)
                css_content += css_response.text

        return html_content, css_content, css_links
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        return None, None, None


def save_to_files(content, filename, extension):
    if content:
        with open(f'{filename}.{extension}', 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"{extension.upper()} content saved to '{filename}.{extension}'.")


def extract_links(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)]
    return links


def run(url, base_filename):
    # Create a list to store visited links
    visited_links = set()

    # List to store all links
    all_links = [url]

    while all_links:
        link = all_links.pop(0)
        parsed_url = urlparse(link)
        domain_path = parsed_url.netloc + parsed_url.path
        filename = os.path.join(base_filename, domain_path)

        # Create directories if they don't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        html_content, css_content, page_links = extract_html_and_css(link)

        # Save the page
        save_to_files(html_content, filename, 'html')
        save_to_files(css_content, filename, 'css')

        visited_links.add(link)  # Mark the current link as visited

        # Extract links from the HTML content
        page_links = extract_links(html_content, link)

        # Add new links to the list
        for new_link in page_links:
            if new_link not in visited_links:
                all_links.append(new_link)


if __name__ == '__main__':
    main_base_url = input("Enter the base URL: ")
    main_base_filename = input("Enter a base filename (without extension): ")

    run(main_base_url, main_base_filename)
