import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import azure.functions as func

from shared.storage import get_pings_last_24h
from shared.config import get_allowed_origins


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered function.

    Returns the last N hours of ping data as JSON.
    Default is 24 hours. The frontend (React dashboard) uses this as its API.

    Example:
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

    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=period_hours)

    filtered: List[Dict[str, Any]] = []
    for record in all_recent:
        ts_str = record.get("timestamp")
        try:
            ts = datetime.fromisoformat(ts_str)
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
