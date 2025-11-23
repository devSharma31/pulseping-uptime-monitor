# PulsePing — Serverless Uptime Monitor + Dashboard

[![Azure Functions](https://img.shields.io/badge/Azure%20Functions-Python-blue?logo=azure-functions&logoColor=white)]()
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)]()
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=1a1a1a)]()
[![Status](https://img.shields.io/badge/Project-Learning%20/Portfolio-success)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-informational.svg)](LICENSE)

**PulsePing** is a small serverless uptime monitor I built to practise:

- Azure Functions (Timer + HTTP trigger)
- Azure Blob Storage (via Azurite locally)
- Python + `httpx`
- React + a simple dashboard for non-technical users

The idea is simple:

> A timer function pings a list of URLs, logs to Blob Storage,  
> an HTTP function exposes the last 24h as JSON,  
> and a small React UI shows uptime %, recent checks, and CSV export.

---

## 1. Tech Stack

### Backend

- ⚡ **Azure Functions v4**
  - Timer trigger: `ping_timer`
  - HTTP trigger: `get_status`
- 🐍 **Python**
  - `httpx` for HTTP requests
  - `azure-storage-blob` for Blob Storage
- 🗄️ **Azure Blob Storage**
  - In local dev: [Azurite](https://github.com/Azure/Azurite) emulator

### Frontend

- ⚛️ **React 18** (Vite)
- Fetch API
- Simple custom CSS (no UI library)

---

## 2. What PulsePing Actually Does

**Backend flow:**

1. **Timer trigger** (`ping_timer`)
   - Runs on a CRON schedule.
   - Reads URLs from `PULSEPING_URLS` (comma-separated).
   - Uses `httpx` to ping each URL.
   - Logs each check as one JSON line:

     ```json
     {
       "timestamp": "2025-11-22T14:34:08.792232+00:00",
       "url": "https://google.com",
       "status_code": 301,
       "is_up": true,
       "response_ms": 85.2
     }
     ```

   - Appends to a daily blob:  
     `pulseping-logs/pings-YYYY-MM-DD.jsonl`

2. **HTTP trigger** (`get_status`)
   - Accepts a query parameter: `hours` (default: `24`)
   - Reads blob(s) for the last N hours, parses JSON lines.
   - Returns a JSON payload:

     ```json
     {
       "generated_at": "2025-11-22T14:46:12.722044+00:00",
       "period_hours": 24,
       "total_checks": 26,
       "checks": [ /* array of log entries */ ]
     }
     ```

**Frontend flow:**

- Calls `GET /api/status?hours=24` from the Functions backend.
- Shows:
  - **Summary cards**: monitored URLs, total checks, average uptime.
  - **Uptime by URL**: total checks, up count, avg latency, uptime % with coloured badges.
  - **Recent checks**: timestamp, URL, HTTP status, UP/DOWN, response time.
  - **Filter by URL** (for the checks table).
- “**Download CSV**” button:
  - Converts current `checks` into `pulseping-<hours>h-export.csv`
  - Designed so someone in support/ops can attach it to tickets.

This is intentionally more “L1/L2 cloud support tool” than “fancy SRE platform”.

---

## 3. Repo Structure

```text
pulseping-uptime-monitor/
├── README.md
├── LICENSE
├── .gitignore
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
    │   ├── config.py           # config & URL helpers
    │   └── storage.py          # Blob read/write helpers
    ├── ping_timer/             # Timer-triggered uptime check
    │   ├── __init__.py
    │   └── function.json
    └── get_status/             # HTTP API for dashboard
        ├── __init__.py
        └── function.json
```
        
## 4. Running the Backend (Functions + Azurite)

4.1 Prereqs

- Python 3.10+
- Node.js + npm
- Azure Functions Core Tools v4 (func)
- Azurite

4.2 Start Azurite

- Install (once):
```
npm install -g azurite
```
- Run in a separate terminal:
```
azurite --silent --location C:\azurite --debug C:\azurite\debug.log
```
- Azurite endpoints (default):
Blob: http://127.0.0.1:10000/devstoreaccount1
Keep this process running.


4.3 local.settings.json (local-only):

Inside functions/, create local.settings.json
```
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
    "FUNCTIONS_WORKER_RUNTIME": "python",

    "PULSEPING_STORAGE_CONNECTION": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
    "PULSEPING_CONTAINER_NAME": "pulseping-logs",

    "PULSEPING_URLS": "https://google.com,https://github.com",
    "PULSEPING_ALLOWED_ORIGINS": "http://localhost:5173"
  }
}
```

- Change PULSEPING_URLS to whatever you want to monitor.
- In a real Azure deployment, these would be real connection strings in App Settings.

4.4 Start Functions locally:
```
cd functions

python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt

func start
```

Now:

- HTTP API: http://localhost:7071/api/status
- Timer trigger will start writing blobs to Azurite (pulseping-logs container).
```
curl http://localhost:7071/api/status
```

## 5. Running the React Dashboard
```
cd dashboard
npm install
npm run dev
```
Open:
```
http://localhost:5173
```
The dashboard assumes the backend is at:
```
// src/App.jsx
const API_BASE_URL = "http://localhost:7071";
```
If you deploy Functions, update that to your real URL, e.g.:
```
const API_BASE_URL = "https://<your-function-app>.azurewebsites.net";
```

## 6. Deployment (High-Level)
If I were to deploy this for real:

1. Azure Functions

- Create a Storage Account and a Python Azure Function App.
- Set App Settings to mirror local.settings.json keys:
   - AzureWebJobsStorage
   - PULSEPING_STORAGE_CONNECTION
   - PULSEPING_CONTAINER_NAME
   - PULSEPING_URLS
   - PULSEPING_ALLOWED_ORIGINS
- Deploy functions/ with VS Code or:
```
func azure functionapp publish <your-function-app-name>
```

2. Frontend
   - Build:
```
cd dashboard
npm run build
```
- Deploy dist/ to Azure Static Web Apps, Blob static site, Netlify, Vercel, etc.
- Update API_BASE_URL to point to the deployed Functions URL.


## 7. License
This project is licensed under the MIT License.
See LICENSE for details.

