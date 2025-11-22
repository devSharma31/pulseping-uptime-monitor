import os

# Default URLs if environment variable is not set.
DEFAULT_MONITORED_URLS = [
    "https://example.com",
    "https://example.org"
]


def get_monitored_urls():
    """
    Returns a list of URLs to monitor.

    You can configure them via the PULSEPING_URLS environment variable:
      PULSEPING_URLS="https://site1.com,https://site2.com"
    """
    raw = os.getenv("PULSEPING_URLS", "").strip()
    if not raw:
        return DEFAULT_MONITORED_URLS

    urls = [u.strip() for u in raw.split(",") if u.strip()]
    return urls or DEFAULT_MONITORED_URLS


def get_storage_connection_string():
    """
    Returns the connection string for Azure Blob Storage.

    Uses PULSEPING_STORAGE_CONNECTION. If you don't set it,
    AzureWebJobsStorage may also work for local dev,
    but in production you'd normally use a dedicated account.
    """
    return os.getenv("PULSEPING_STORAGE_CONNECTION") or os.getenv("AzureWebJobsStorage")


def get_container_name():
    """
    Returns the blob container name used to store ping logs.
    """
    return os.getenv("PULSEPING_CONTAINER_NAME", "pulseping-logs")


def get_allowed_origins():
    """
    Returns a comma-separated string of allowed origins for CORS.
    Example:
      PULSEPING_ALLOWED_ORIGINS="http://localhost:5173,https://myapp.com"
    """
    return os.getenv("PULSEPING_ALLOWED_ORIGINS", "*")
