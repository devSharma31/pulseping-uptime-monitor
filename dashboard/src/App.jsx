import React, { useEffect, useMemo, useState } from "react";

// backend URL (local Functions)
const API_BASE_URL = "http://localhost:7071";

function App() {
  const [data, setData] = useState(null);
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedUrl, setSelectedUrl] = useState("all");

  const fetchData = async (selectedHours = hours) => {
    try {
      setLoading(true);
      setError("");

      const url = `${API_BASE_URL}/api/status?hours=${selectedHours}`;
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`API returned status ${res.status}`);
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error("Failed to fetch status:", err);
      setError("Could not load data from the API. Check Functions + Azurite.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(24);
  }, []);

  // group checks by URL and calculate uptime
  const uptimeByUrl = useMemo(() => {
    if (!data || !data.checks) return {};

    const perUrl = {};

    for (const check of data.checks) {
      const url = check.url;
      if (!perUrl[url]) perUrl[url] = { total: 0, up: 0, latencies: [] };

      perUrl[url].total += 1;
      if (check.is_up) perUrl[url].up += 1;
      if (typeof check.response_ms === "number") {
        perUrl[url].latencies.push(check.response_ms);
      }
    }

    const result = {};
    for (const [url, stats] of Object.entries(perUrl)) {
      const uptimePct =
        stats.total === 0 ? 0 : (stats.up / stats.total) * 100;

      const avgLatency =
        stats.latencies.length === 0
          ? null
          : stats.latencies.reduce((a, b) => a + b, 0) /
            stats.latencies.length;

      result[url] = {
        total: stats.total,
        up: stats.up,
        uptimePercent: Math.round(uptimePct * 10) / 10,
        avgLatency: avgLatency ? Math.round(avgLatency) : null
      };
    }

    return result;
  }, [data]);

  const urlsList = useMemo(
    () => Object.keys(uptimeByUrl),
    [uptimeByUrl]
  );

  const handleDownloadCsv = () => {
    if (!data || !data.checks || data.checks.length === 0) {
      alert("No data to export yet.");
      return;
    }

    const headers = [
      "timestamp",
      "url",
      "status_code",
      "is_up",
      "response_ms"
    ];

    const rows = data.checks.map((check) => [
      check.timestamp,
      check.url,
      check.status_code,
      check.is_up,
      check.response_ms
    ]);

    const csvLines = [
      headers.join(","),
      ...rows.map((r) =>
        r
          .map((value) => {
            if (value === null || value === undefined) return "";
            const v = String(value);
            if (v.includes(",") || v.includes('"')) {
              return `"${v.replace(/"/g, '""')}"`;
            }
            return v;
          })
          .join(",")
      )
    ];

    const csvContent = csvLines.join("\n");
    const blob = new Blob([csvContent], {
      type: "text/csv;charset=utf-8;"
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute(
      "download",
      `pulseping-${hours}h-export.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleHoursChange = (e) => {
    const value = Number(e.target.value) || 24;
    setHours(value);
  };

  const handleApplyHours = () => {
    fetchData(hours);
  };

  const handleRefresh = () => {
    fetchData(hours);
  };

  const handleUrlFilterChange = (e) => {
    setSelectedUrl(e.target.value);
  };

  const filteredChecks =
    data && data.checks
      ? data.checks.filter((c) =>
          selectedUrl === "all" ? true : c.url === selectedUrl
        )
      : [];

  const totalUrls = urlsList.length;
  const totalChecks = data?.total_checks || 0;
  const overallUptime =
    totalUrls === 0
      ? 0
      : Math.round(
          (Object.values(uptimeByUrl).reduce(
            (acc, item) => acc + item.uptimePercent,
            0
          ) /
            totalUrls) *
            10
        ) / 10;

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <span className="logo-dot" />
          <span className="brand-text">PulsePing</span>
        </div>
        <span className="topbar-tagline">
          Tiny uptime monitor • Azure Functions + React • Built by Dev
        </span>
      </header>

      <main className="container">
        <section className="hero-card">
          <div>
            <h1>Uptime Monitor</h1>
            <p className="subtitle">
              Simple checks, clear logs and a small dashboard – exactly what
              you&apos;d expect from an L1/L2 cloud support tool.
            </p>
          </div>

          <div className="period-controls">
            <label>
              Period (hours)
              <input
                type="number"
                min="1"
                max="48"
                value={hours}
                onChange={handleHoursChange}
              />
            </label>
            <button onClick={handleApplyHours} disabled={loading}>
              Apply
            </button>
            <button onClick={handleRefresh} disabled={loading}>
              Refresh
            </button>
            <button onClick={handleDownloadCsv} disabled={loading}>
              Download CSV
            </button>
          </div>

          {data && (
            <p className="meta">
              Showing last <strong>{data.period_hours}h</strong>. Total
              checks: <strong>{data.total_checks}</strong>. Generated at{" "}
              <code>{data.generated_at}</code>.
            </p>
          )}

          {loading && <p className="info">Loading data…</p>}
          {error && <p className="error">{error}</p>}
        </section>

        {/* summary cards */}
        <section className="summary-row">
          <div className="summary-card">
            <span className="summary-label">Monitored URLs</span>
            <span className="summary-value">{totalUrls}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">Total checks (period)</span>
            <span className="summary-value">{totalChecks}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">Avg uptime across URLs</span>
            <span className="summary-value">
              {overallUptime ? `${overallUptime}%` : "—"}
            </span>
          </div>
        </section>

        {/* uptime by URL */}
        <section className="card">
          <div className="card-header">
            <h2>Uptime by URL</h2>
          </div>

          {data && filteredChecks.length > 0 ? (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>URL</th>
                    <th>Total Checks</th>
                    <th>Up</th>
                    <th>Avg Latency (ms)</th>
                    <th>Uptime %</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(uptimeByUrl).map(
                    ([url, stats]) => (
                      <tr key={url}>
                        <td>{url}</td>
                        <td>{stats.total}</td>
                        <td>{stats.up}</td>
                        <td>
                          {stats.avgLatency !== null
                            ? stats.avgLatency
                            : "—"}
                        </td>
                        <td>
                          <span
                            className={
                              stats.uptimePercent >= 99
                                ? "badge badge-good"
                                : stats.uptimePercent >= 95
                                ? "badge badge-warn"
                                : "badge badge-bad"
                            }
                          >
                            {stats.uptimePercent}%
                          </span>
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="info">
              Waiting for timer function to generate some checks…
            </p>
          )}
        </section>

        {/* recent checks with URL filter */}
        <section className="card">
          <div className="card-header">
            <h2>Recent Checks</h2>
            <div className="filter-row">
              <label>
                Filter by URL
                <select
                  value={selectedUrl}
                  onChange={handleUrlFilterChange}
                >
                  <option value="all">All URLs</option>
                  {urlsList.map((url) => (
                    <option key={url} value={url}>
                      {url}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          {filteredChecks && filteredChecks.length > 0 ? (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Timestamp (UTC)</th>
                    <th>URL</th>
                    <th>Status</th>
                    <th>Up?</th>
                    <th>Response (ms)</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredChecks.map((check, idx) => (
                    <tr key={idx}>
                      <td>
                        <code>{check.timestamp}</code>
                      </td>
                      <td>{check.url}</td>
                      <td>{check.status_code}</td>
                      <td
                        className={
                          check.is_up ? "status up" : "status down"
                        }
                      >
                        {check.is_up ? "UP" : "DOWN"}
                      </td>
                      <td>{check.response_ms}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="info">
              No checks in this period for the selected filter.
            </p>
          )}
        </section>

        <footer className="footer">
          <span>
            PulsePing • built as a learning project by Devashish
            Sharma (Azure Functions + React).
          </span>
        </footer>
      </main>
    </div>
  );
}

export default App;
