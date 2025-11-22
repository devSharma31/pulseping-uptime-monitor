import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError

from .config import get_storage_connection_string, get_container_name


def _get_blob_service_client() -> BlobServiceClient:
    """
    Creates a BlobServiceClient using the configured connection string.
    """
    connection_string = get_storage_connection_string()
    if not connection_string:
        raise RuntimeError("No storage connection string configured for PulsePing.")
    return BlobServiceClient.from_connection_string(connection_string)


def _get_container_client():
    """
    Returns a container client for the configured container.
    Creates the container if it does not exist.
    """
    service_client = _get_blob_service_client()
    container_name = get_container_name()
    container_client = service_client.get_container_client(container_name)

    try:
        container_client.create_container()
    except Exception:
        # Container already exists or another harmless error.
        pass

    return container_client


def _get_blob_name_for_date(date: datetime) -> str:
    """
    Returns the blob name for a given UTC date.
    Format: pings-YYYY-MM-DD.jsonl
    """
    date_str = date.strftime("%Y-%m-%d")
    return f"pings-{date_str}.jsonl"


def save_ping_result(result: Dict) -> None:
    """
    Appends a single ping result to today's blob as a JSON line.

    This implementation is intentionally simple for a small demo:
      - Download the existing blob (if any)
      - Append a line
      - Upload it back with overwrite=True
    """
    container_client = _get_container_client()

    now_utc = datetime.now(timezone.utc)
    blob_name = _get_blob_name_for_date(now_utc)
    blob_client = container_client.get_blob_client(blob_name)

    line = json.dumps(result) + "\n"

    # Try to read existing content (if the blob already exists)
    try:
        blob_data = blob_client.download_blob().readall()
        existing_text = blob_data.decode("utf-8")
    except ResourceNotFoundError:
        existing_text = ""

    new_text = existing_text + line
    blob_client.upload_blob(new_text.encode("utf-8"), overwrite=True)


def get_pings_last_24h() -> List[Dict]:
    """
    Returns all ping results from the last 24 hours.

    We fetch today's and yesterday's blobs (if they exist),
    parse each JSON line, and filter by timestamp >= (now - 24h).
    """
    container_client = _get_container_client()
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=24)

    dates_to_check = [
        now_utc,
        now_utc - timedelta(days=1),
    ]

    results: List[Dict] = []

    for date in dates_to_check:
        blob_name = _get_blob_name_for_date(date)
        blob_client = container_client.get_blob_client(blob_name)

        try:
            blob_data = blob_client.download_blob().readall()
        except ResourceNotFoundError:
            # No logs for this date.
            continue

        text = blob_data.decode("utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                # Ignore malformed lines
                continue

            ts_str = record.get("timestamp")
            try:
                record_ts = datetime.fromisoformat(ts_str)
            except Exception:
                continue

            if record_ts.tzinfo is None:
                record_ts = record_ts.replace(tzinfo=timezone.utc)

            if record_ts >= cutoff:
                results.append(record)

    # Sort ascending by timestamp for nicer display
    results.sort(key=lambda r: r.get("timestamp", ""))

    return results
