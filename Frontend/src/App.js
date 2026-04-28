import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, NavLink } from "react-router-dom";
import AuditForm from "./components/AuditForm";
import ChartView from "./components/ChartView";
import ResultTable from "./components/ResultTable";
import "./styles/App.css";

// ── Screen 1: Results Dashboard ───────────────────────────────────
function Dashboard() {
  const [auditResult, setAuditResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  return (
    <div className="page">
      <p className="section-label">Fairness Unit Testing</p>
      <h2 className="page-title">Run Fairness Audit</h2>
      <p className="page-sub">
        Configure an identity experiment, then run a controlled audit to detect bias.
      </p>

      {/* Input form */}
      <AuditForm
        onResult={(result) => { setError(null); setAuditResult(result); }}
        onLoading={setLoading}
        onError={setError}
      />

      {/* Loading state */}
      {loading && (
        <div className="empty-state" style={{ marginTop: "32px" }}>
          <span className="spinner" style={{ width: 24, height: 24 }} />
          <p>Running controlled identity experiments…</p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="error-box" style={{ marginTop: "20px" }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {auditResult && !loading && (
        <div className="results-grid">
          {/* Stat cards */}
          <div className="metric-grid">
            <StatCard
              label="ISS Score"
              value={auditResult.iss_score.toFixed(3)}
              sub="Identity Sensitivity Score"
              highlight={auditResult.iss_score > 0.05}
            />
            <StatCard
              label="p-value"
              value={auditResult.p_value.toFixed(4)}
              sub={auditResult.p_value < 0.05 ? "Significant ✓" : "Not significant"}
              highlight={auditResult.p_value < 0.05}
            />
            <StatCard
              label="95% CI"
              value={`[${auditResult.confidence_interval[0].toFixed(2)}, ${auditResult.confidence_interval[1].toFixed(2)}]`}
              sub="Bootstrap confidence interval"
              highlight={
                auditResult.confidence_interval[0] > 0 ||
                auditResult.confidence_interval[1] < 0
              }
            />
            <VerdictCard verdict={auditResult.verdict} />
          </div>

          {/* Score chart */}
          <div className="card">
            <div className="card-title">Score Distribution</div>
            <ChartView result={auditResult} />
          </div>

          {/* Full result table */}
          <ResultTable result={auditResult} />
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, sub, highlight }) {
  return (
    <div className={`metric-card ${highlight ? "metric-card--alert" : ""}`}>
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-sub">{sub}</p>
    </div>
  );
}

function VerdictCard({ verdict }) {
  const isDetected = verdict !== "no_significant_difference";
  return (
    <div className={`metric-card verdict-card ${isDetected ? "metric-card--alert" : "metric-card--ok"}`}>
      <p className="metric-label">Verdict</p>
      <p className="metric-value" style={{ fontSize: "14px", lineHeight: 1.4, marginTop: "4px" }}>
        {verdict.replace(/_/g, " ")}
      </p>
    </div>
  );
}

// ── Screen 2: API Simulator ───────────────────────────────────────
const DEFAULT_REQUEST_STR = JSON.stringify(
  {
    target: { type: "seeded" },
    base_input: "Candidate with 4 years of Python and Django experience.",
    identity_variable: "gender",
    sample_size: 50,
  },
  null,
  2
);

function ApiSimulator() {
  const [requestText, setRequestText] = useState(DEFAULT_REQUEST_STR);
  const [response, setResponse]       = useState(null);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);

  async function handleSend() {
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const body = JSON.parse(requestText);
      const BASE_URL = process.env.REACT_APP_API_URL || "";
      const res = await fetch(`${BASE_URL}/audit`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || `HTTP ${res.status}`);
      setResponse(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <p className="section-label">Developer Tools</p>
      <h2 className="page-title">API Simulator</h2>
      <p className="page-sub">
        Send a live <code>POST /audit</code> request and inspect the raw JSON response.
      </p>

      <div className="simulator-grid">
        {/* Left: request editor */}
        <div className="sim-panel">
          <div className="sim-panel-header">
            <div>
              <span className="sim-method">POST</span>
              <span className="sim-path">/audit</span>
            </div>
          </div>
          <textarea
            className="sim-code"
            value={requestText}
            onChange={(e) => setRequestText(e.target.value)}
            spellCheck={false}
            style={{ minHeight: "320px" }}
          />
          <button
            className="btn btn-primary sim-run-btn"
            onClick={handleSend}
            disabled={loading}
          >
            {loading ? "Running audit…" : "▶  Send Request"}
          </button>
        </div>

        {/* Right: response panel */}
        <div className="sim-panel">
          <div className="sim-panel-header">
            <span
              style={{
                fontSize: "11px",
                fontWeight: 600,
                letterSpacing: "0.1em",
                color: response ? "var(--green)" : error ? "var(--red)" : "var(--text-muted)",
              }}
            >
              {response ? "200 OK" : error ? "Error" : "Awaiting response"}
            </span>
          </div>
          <pre className="sim-code" style={{ minHeight: "320px" }}>
            {error
              ? `// Error\n${error}`
              : response
              ? JSON.stringify(response, null, 2)
              : "// Response will appear here"}
          </pre>
        </div>
      </div>
    </div>
  );
}

// ── Root App ──────────────────────────────────────────────────────
export default function App() {
  return (
    <Router>
      <div className="app-root">
        {/* Top nav */}
        <header className="nav">
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span className="brand-icon">⚖</span>
            <span className="brand-name">DHARITRI</span>
            <span className="brand-tag">Fairness Unit Testing for AI</span>
          </div>
          <nav className="nav-tabs">
            <NavLink
              to="/"
              end
              className={({ isActive }) => (isActive ? "nav-tab active" : "nav-tab")}
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/simulator"
              className={({ isActive }) => (isActive ? "nav-tab active" : "nav-tab")}
            >
              API Simulator
            </NavLink>
          </nav>
        </header>

        {/* Routes — no extra .page wrapper here; each screen renders its own */}
        <main style={{ flex: 1 }}>
          <Routes>
            <Route path="/"          element={<Dashboard />} />
            <Route path="/simulator" element={<ApiSimulator />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}