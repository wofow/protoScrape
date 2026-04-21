from urllib.parse import urlparse


def is_valid_url(url):
    """Check if URL is valid (http/https) and has a non-empty host."""
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
