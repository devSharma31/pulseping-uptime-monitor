# PulsePing — Serverless Uptime Monitor + Dashboard

**PulsePing** is a small, realistic uptime monitoring project:

- An **Azure Functions** timer trigger pings a list of URLs on a schedule.
- Each check logs: timestamp, URL, status code, up/down flag, response time.
- Results are stored as JSON lines in **Azure Blob Storage** (Azurite in local dev).
- An **HTTP-triggered Function** exposes the last 24 hours of checks as JSON.
- A **React dashboard** calls that API, shows uptime %, and lets you download a **CSV**.

---

## Tech stack

**Backend**

- Azure Functions (v4) — Timer trigger + HTTP trigger
- Python
- [`httpx`](https://www.python-httpx.org/) for HTTP pings
- Azure Blob Storage via [`azure-storage-blob`](https://pypi.org/project/azure-storage-blob/)
- [Azurite](https://github.com/Azure/Azurite) for local storage emulation

**Frontend**

- React 18 (Vite)
- Fetch API
- Simple custom CSS

---

## High-level architecture

1. **Timer function** (`ping_timer`)
   - Runs on a CRON schedule (e.g. every minute in dev).
   - Pings each URL from `PULSEPING_URLS` using `httpx`.
   - Appends a JSON line to a daily blob in the configured container, e.g.:  
     `pulseping-logs/pings-2025-11-22.jsonl`.

2. **HTTP function** (`get_status`)
   - Reads blobs for the last N hours (default: 24).
   - Streams + filters JSON lines.
   - Returns a response of the form:

     ```json
     {
       "generated_at": "2025-11-22T14:46:12.722044+00:00",
       "period_hours": 24,
       "total_checks": 26,
       "checks": [
         {
           "timestamp": "2025-11-22T14:34:08.792232+00:00",
           "url": "https://google.com",
           "status_code": 301,
           "is_up": true,
           "response_ms": 85.2
         }
       ]
     }
     ```

3. **React dashboard** (`dashboard/`)
   - Calls `GET /api/status?hours=24`.
   - Shows:
     - **Summary cards** (monitored URLs, total checks, average uptime).
     - **Uptime by URL** table (total checks, up count, avg latency, uptime % with badges).
     - **Recent checks** table with optional URL filter.
   - “Download CSV” exports the checks as `pulseping-<hours>h-export.csv` for tickets/incident review.

---

## Project structure

```text
pulseping-uptime-monitor/
├── README.md
├── .gitignore
├── LICENSE
├── dashboard/                  # React dashboard (Vite)
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       └── styles.css
└── functions/                  # Azure Functions backend (Python)
    ├── host.json
    ├── local.settings.example.json
    ├── requirements.txt
    ├── shared/
    │   ├── __init__.py
    │   ├── config.py           # URL list + config helpers
    │   └── storage.py          # Blob read/write helpers
    ├── ping_timer/             # Timer-triggered function
    │   ├── __init__.py
    │   └── function.json
    └── get_status/             # HTTP-triggered function
        ├── __init__.py
        └── function.json

```
## Running the backend (Azure Functions + Azurite)

1. Prerequisites:

- Python 3.10+
- Node.js + npm
- Azure Functions Core Tools v4 (func CLI)
- Azurite (via npm)

2. Start Azurite:

- Install (once):
```
npm install -g azurite
```
Run in a separate terminal:
```
azurite --silent --location C:\azurite --debug C:\azurite\debug.log

```

