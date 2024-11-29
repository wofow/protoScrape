from urllib.parse import urlparse


def is_valid_url(url):
    """Check if URL is valid and belongs to same domain."""
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and parsed.netloc != ''