import urllib.request

def get(url: str) -> str:
    """Simple HTTP GET request (returns text)."""
    with urllib.request.urlopen(url) as r:
        return r.read().decode("utf-8")

def wget(url: str, path: str):
    """Download file from URL to path."""
    urllib.request.urlretrieve(url, path)
    return path
