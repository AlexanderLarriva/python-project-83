from urllib.parse import urlparse


def normalize_url(input_url):
    parsed_url = urlparse(input_url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"
