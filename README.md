# PulsePing — Serverless Uptime Monitor + Dashboard

**PulsePing** is a small, realistic uptime monitoring tool:

- An **Azure Functions** timer trigger pings a list of URLs every few minutes.
- Each check logs: timestamp, URL, status code, up/down flag, and response time.
- Results are stored as JSON lines in **Azure Blob Storage** (using Azurite locally).
- An **HTTP-triggered Azure Function** exposes the last 24 hours of checks as JSON.
- A **React dashboard** calls that API, shows uptime %, and offers a **CSV export** for incidents.

This matches the CV line:

> **PulsePing — Serverless Uptime Monitor + Dashboard**  
> Stack: Azure Functions (Timer/HTTP), Python httpx, Azure Blob/Table, React/static JS  
> Set up Azure Functions to ping URLs every few minutes and store status and latency in Azure Storage.  
> Built a small front-end dashboard to show 24-hour history and uptime %, with CSV export so non-technical users can review incidents.

---

## Stack

**Backend**

- Azure Functions (v4)
  - Timer trigger (`ping_timer`)
  - HTTP trigger (`get_status`)
- Python
- [`httpx`](https://www.python-httpx.org/) for HTTP checks
- Azure Blob Storage (via [`azure-storage-blob`](https://pypi.org/project/azure-storage-blob/))
- Azurite for local emulator (no paid Azure subscription required)

**Frontend**

- React 18 (via Vite)
- Fetch API for HTTP calls
- Simple CSS (no heavy UI framework)

---

## What this shows about me as a candidate

This project is deliberately small but realistic. It shows that I can:

- Work with **serverless architectures** on Azure (triggers, bindings, app settings).
- Design a simple **monitoring workflow**:
  - Schedule checks with a timer trigger.
  - Log data in a consistent, append-only format.
  - Expose a clean **read API** on top of the logs.
- Use **Azure Storage (Blob)** via the official Python SDK.
- Build a **dashboard for non-technical stakeholders**:
  - Uptime % per URL.
  - Recent checks with timestamps and response times.
  - CSV export for incident review, tickets, or management reports.
- Think like an **IT Support / Cloud Support engineer**:
  - Clear timestamps and statuses.
  - Simple JSON payloads.
  - Easy handover to another engineer (config-driven URLs, obvious structure).

---

## Project structure

```text
pulseping-uptime-monitor/
├── README.md
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
    │   ├── config.py           # URL list + general config helpers
    │   └── storage.py          # Blob read/write helpers
    ├── ping_timer/             # Timer-triggered function
    │   ├── __init__.py
    │   └── function.json
    └── get_status/             # HTTP-triggered function
        ├── __init__.py
        └── function.json
