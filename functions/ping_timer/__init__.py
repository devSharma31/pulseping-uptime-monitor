import datetime
import logging
from datetime import timezone

import azure.functions as func
import httpx

from shared.config import get_monitored_urls
from shared.storage import save_ping_result


def main(mytimer: func.TimerRequest) -> None:
    """
    Timer-triggered function.

    Runs every few minutes and pings each configured URL,
    then stores the result in Azure Blob Storage via save_ping_result().
    """
    utc_now = datetime.datetime.now(timezone.utc)
    logging.info("PulsePing timer trigger started at %s", utc_now.isoformat())

    urls = get_monitored_urls()
    logging.info("Monitoring %d URLs: %s", len(urls), ", ".join(urls))

    # Simple synchronous httpx client is enough for a small list of URLs.
    with httpx.Client(timeout=10.0) as client:
        for url in urls:
            _ping_and_store(client, url)

    logging.info("PulsePing timer trigger finished.")


def _ping_and_store(client: httpx.Client, url: str) -> None:
    """
    Sends a single HTTP GET request to the given URL and stores the result.

    The stored record includes:
      - timestamp (UTC)
      - url
      - status_code
      - is_up (True/False)
      - response_ms (response time in milliseconds, or None on failure)
    """
    start = datetime.datetime.now(timezone.utc)
    try:
        response = client.get(url)
        end = datetime.datetime.now(timezone.utc)

        elapsed_ms = (end - start).total_seconds() * 1000.0
        status_code = response.status_code
        is_up = 200 <= status_code < 400

        logging.info(
            "Ping %s -> status=%d, is_up=%s, response_ms=%.1f",
            url, status_code, is_up, elapsed_ms
        )

        result = {
            "timestamp": start.isoformat(),
            "url": url,
            "status_code": status_code,
            "is_up": is_up,
            "response_ms": round(elapsed_ms, 1),
        }

    except Exception as ex:
        end = datetime.datetime.now(timezone.utc)
        elapsed_ms = (end - start).total_seconds() * 1000.0

        logging.warning("Ping %s failed: %s", url, ex)

        result = {
            "timestamp": start.isoformat(),
            "url": url,
            "status_code": 0,    # 0 = no HTTP status (e.g. DNS failure, timeout)
            "is_up": False,
            "response_ms": round(elapsed_ms, 1),
            "error": str(ex),
        }

    # Store the result in blob storage
    save_ping_result(result)
