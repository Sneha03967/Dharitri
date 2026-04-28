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
    <div className="screen">
      <h2 className="screen-title">Run Fairness Audit</h2>

      {/* Input form */}
      <AuditForm
        onResult={setAuditResult}
        onLoading={setLoading}
        onError={setError}
      />

      {/* Loading state */}
      {loading && (
        <div className="loading-bar">
          <span className="spinner" />
          Running controlled identity experiments…
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="alert alert-danger">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {auditResult && !loading && (
        <div className="results-grid">
          {/* Stat cards */}
          <div className="stat-cards">
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
              value={`[${auditResult.confidence_interval[0].toFixed(3)}, ${auditResult.confidence_interval[1].toFixed(3)}]`}
              sub="Bootstrap confidence interval"
              highlight={
                auditResult.confidence_interval[0] > 0 ||
                auditResult.confidence_interval[1] < 0
              }
            />
            <VerdictCard verdict={auditResult.verdict} />
          </div>

          {/* Score chart */}
          <ChartView result={auditResult} />

          {/* Full result table */}
          <ResultTable result={auditResult} />
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, sub, highlight }) {
  return (
    <div className={`stat-card ${highlight ? "stat-card--alert" : ""}`}>
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
      <p className="stat-sub">{sub}</p>
    </div>
  );
}

function VerdictCard({ verdict }) {
  const isDetected = verdict !== "no_significant_difference";
  return (
    <div className={`stat-card verdict-card ${isDetected ? "stat-card--alert" : "stat-card--ok"}`}>
      <p className="stat-label">Verdict</p>
      <p className="verdict-text">{verdict.replace(/_/g, " ")}</p>
    </div>
  );
}

// ── Screen 2: API Simulator ───────────────────────────────────────
const DEFAULT_REQUEST = JSON.stringify(
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
  const [requestText, setRequestText] = useState(DEFAULT_REQUEST);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSend() {
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const body = JSON.parse(requestText);
      const res  = await fetch("/audit", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || "Request failed");
      setResponse(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="screen">
      <h2 className="screen-title">API Simulator</h2>
      <p className="screen-sub">
        Send a live <code>POST /audit</code> request and inspect the raw JSON response.
      </p>

      <div className="simulator-grid">
        {/* Left: request editor */}
        <div className="sim-panel">
          <div className="sim-panel-header">
            <span className="method-badge">POST</span>
            <span className="endpoint-text">/audit</span>
          </div>
          <textarea
            className="code-editor"
            value={requestText}
            onChange={(e) => setRequestText(e.target.value)}
            spellCheck={false}
            rows={18}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={loading}
          >
            {loading ? "Running audit…" : "▶  Send Request"}
          </button>
        </div>

        {/* Right: response panel */}
        <div className="sim-panel">
          <div className="sim-panel-header">
            <span className={`status-badge ${response ? "status-ok" : error ? "status-err" : "status-idle"}`}>
              {response ? "200 OK" : error ? "Error" : "Awaiting response"}
            </span>
          </div>
          <pre className="code-output">
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
      <div className="app">
        {/* Top nav */}
        <header className="navbar">
          <div className="navbar-brand">
            <span className="brand-icon">⚖</span>
            <span className="brand-name">DHARITRI</span>
            <span className="brand-tag">Fairness Unit Testing for AI</span>
          </div>
          <nav className="navbar-links">
            <NavLink to="/"          className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
              Dashboard
            </NavLink>
            <NavLink to="/simulator" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
              API Simulator
            </NavLink>
          </nav>
        </header>

        {/* Routes */}
        <main className="main-content">
          <Routes>
            <Route path="/"          element={<Dashboard />} />
            <Route path="/simulator" element={<ApiSimulator />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}