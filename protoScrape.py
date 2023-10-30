import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import logging


def extract_html_and_css_recursive(url, visited_links):
    html_content, css_content, page_links = None, None, []
    try:
        if url in visited_links:
            # Skip URLs that have already been visited to avoid infinite loops
            return html_content, css_content, page_links

        visited_links.add(url)

        # Send an HTTP GET request to the URL
        response = requests.get(url)

        # Check the response status code
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract HTML content
            html_content = str(soup)

            # Extract CSS styles
            css_links = []
            css_content = ""
            for link in soup.find_all('link', rel='stylesheet'):
                css_url = link.get('href')
                css_url = urljoin(url, css_url)
                css_response = requests.get(css_url)

                if css_response.status_code == 200:
                    css_links.append(css_url)
                    css_content += css_response.text

            # Extract links from the HTML content
            page_links = extract_links(html_content, url)
            for new_link in page_links:
                extracted_html, extracted_css, _ = extract_html_and_css_recursive(new_link, visited_links)
                html_content += extracted_html
                css_content += extracted_css

        return html_content, css_content, page_links

    except requests.exceptions.RequestException as e:

        error_message = f"Request failed for URL {url}: {str(e)}"
        logging.error(error_message)

        if isinstance(e, requests.exceptions.Timeout):
            logging.error("Timeout error.")

        elif isinstance(e, requests.exceptions.ConnectionError):
            logging.error("Connection error.")

        # Handle other error types as needed

        return html_content, css_content, page_links
    except Exception as ex:
        # Handle other unexpected exceptions
        logging.error(f"An unexpected error occurred for URL {url}: {str(ex)}")
        return html_content, css_content, page_links


def save_to_files(content, filename, extension):
    if content:
        with open(f'{filename}.{extension}', 'w', encoding='utf-8') as file:
            file.write(content)
        logging.info(f"{extension.upper()} content saved to '{filename}.{extension}'.")


def extract_links(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)]

    # Filter out links that don't start with "http" or "https"
    links = [link for link in links if link.startswith('http') or link.startswith('https')]

    return links


def extract_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain


def run(url, base_filename):
    visited_links = set()
    all_links = [url]

    while all_links:
        link = all_links.pop(0)
        domain = extract_domain(link)

        # Use the domain to create a directory structure
        directory_structure = os.path.join(base_filename, domain)
        filename = os.path.join(directory_structure, "index")

        # Create directories if they don't exist
        os.makedirs(directory_structure, exist_ok=True)

        # Send an HTTP GET request to the URL
        response = requests.get(link)

        # Check the response status code
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract HTML content
            html_content = str(soup)

            # Process and save HTML and CSS content
            save_to_files(html_content, filename, 'html')

            # Extract links from the HTML content
            page_links = extract_links(html_content, link)

            # Add new links to the list for further processing
            for new_link in page_links:
                if new_link not in visited_links:
                    all_links.append(new_link)

        visited_links.add(link)


if __name__ == '__main__':
    # Initialize logging
    logging.basicConfig(filename='web_scraping.log', level=logging.INFO)

    main_base_url = input("Enter the base URL: ")
    run(main_base_url, main_base_url)
