"""
PulsePing - Azure Functions app (Python v2 programming model).

- ping_timer: timer trigger, pings each monitored URL and appends the result to Blob Storage.
- get_status: HTTP trigger, GET /api/status?hours=N returns the last N hours of checks as JSON.
"""
import json
import logging
from datetime import datetime as dt, timedelta, timezone
from typing import Any, Dict, List

import azure.functions as func
import httpx

from shared.config import get_allowed_origins, get_monitored_urls
from shared.storage import get_pings_last_24h, save_ping_result

app = func.FunctionApp()

# Every hour. Frequent enough for a demo, small enough to stay
# inside the Flex Consumption free grant (and to let scale-to-zero
# targets actually scale to zero between checks).
PING_SCHEDULE = "0 0 * * * *"


@app.timer_trigger(schedule=PING_SCHEDULE, arg_name="mytimer", run_on_startup=False)
def ping_timer(mytimer: func.TimerRequest) -> None:
    """Pings each configured URL and stores the result in Blob Storage."""
    utc_now = dt.now(timezone.utc)
    logging.info("PulsePing timer trigger started at %s", utc_now.isoformat())

    urls = get_monitored_urls()
    logging.info("Monitoring %d URLs: %s", len(urls), ", ".join(urls))

    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
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
    start = dt.now(timezone.utc)
    try:
        response = client.get(url)
        end = dt.now(timezone.utc)

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
        end = dt.now(timezone.utc)
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


@app.route(route="status", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_status(req: func.HttpRequest) -> func.HttpResponse:
    """
    Returns the last N hours of ping data as JSON (default 24, max 48).

      GET /api/status
      GET /api/status?hours=12
    """
    logging.info("PulsePing get_status function processed a request.")

    # Read optional 'hours' query parameter
    hours_param = req.params.get("hours")
    try:
        period_hours = int(hours_param) if hours_param else 24
    except ValueError:
        period_hours = 24

    if period_hours <= 0 or period_hours > 48:
        # Keep it simple and safe: cap between 1 and 48 hours
        period_hours = 24

    # Fetch data (currently always 24h) and re-filter to the requested period
    all_recent = get_pings_last_24h()

    now_utc = dt.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=period_hours)

    filtered: List[Dict[str, Any]] = []
    for record in all_recent:
        ts_str = record.get("timestamp")
        try:
            ts = dt.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            continue

        if ts >= cutoff:
            filtered.append(record)

    payload = {
        "generated_at": now_utc.isoformat(),
        "period_hours": period_hours,
        "total_checks": len(filtered),
        "checks": filtered,
    }

    body = json.dumps(payload, indent=2)

    allowed_origins = get_allowed_origins()

    return func.HttpResponse(
        body,
        status_code=200,
        mimetype="application/json",
        headers={
            "Access-Control-Allow-Origin": allowed_origins,
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

