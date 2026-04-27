import React from 'react';

/**
 * ResultTable — displays the full statistical audit output.
 *
 * Props:
 *   result — AuditResult object from the backend
 */
export default function ResultTable({ result }) {
  if (!result) {
    return (
      <div className="empty-state">
        <div className="empty-icon">◎</div>
        <p>No audit results yet. Fill in the form and run an audit to see statistical output here.</p>
      </div>
    );
  }

  const {
    iss_score,
    p_value,
    confidence_interval,
    verdict,
    mean_score_group_a,
    mean_score_group_b,
    n_samples_per_group,
    description,
  } = result;

  const [ci_low, ci_high] = confidence_interval;
  const verdictMeta = getVerdictMeta(verdict);

  return (
    <div>
      {/* Verdict banner */}
      <div className={`verdict-banner ${verdictMeta.cls}`}>
        <span className="verdict-dot" />
        {verdictMeta.label}
      </div>

      {/* Key metrics */}
      <div className="metric-grid" style={{ marginBottom: '24px' }}>
        <MetricCard
          label="ISS Score"
          value={iss_score.toFixed(4)}
          sub="0 = no sensitivity"
          accent={issAccent(iss_score)}
        />
        <MetricCard
          label="p-value"
          value={p_value.toFixed(4)}
          sub={p_value < 0.05 ? '< 0.05 — significant' : '≥ 0.05 — not significant'}
          accent={p_value < 0.05 ? 'var(--red)' : 'var(--green)'}
        />
        <MetricCard
          label="Score gap"
          value={`${(mean_score_group_a - mean_score_group_b).toFixed(1)} pts`}
          sub={`${mean_score_group_a.toFixed(1)} vs ${mean_score_group_b.toFixed(1)}`}
          accent="var(--amber)"
        />
      </div>

      {/* CI visualisation */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div className="card-title">95% Bootstrap Confidence Interval</div>
        <CIBar low={ci_low} high={ci_high} />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
          <span>Lower: {ci_low.toFixed(3)}</span>
          <span style={{ color: ciCrossesZero(ci_low, ci_high) ? 'var(--amber)' : 'var(--accent)' }}>
            {ciCrossesZero(ci_low, ci_high) ? 'CI crosses zero — effect uncertain' : 'CI excludes zero — effect is real'}
          </span>
          <span>Upper: {ci_high.toFixed(3)}</span>
        </div>
      </div>

      {/* Detail table */}
      <div className="card">
        <div className="card-title">Audit details</div>
        <table className="result-table">
          <tbody>
            <Row label="Experiment"         value={description} />
            <Row label="Samples per group"  value={n_samples_per_group} />
            <Row label="Group A avg score"  value={`${mean_score_group_a.toFixed(2)} / 100`} />
            <Row label="Group B avg score"  value={`${mean_score_group_b.toFixed(2)} / 100`} />
            <Row label="ISS score"          value={iss_score.toFixed(6)} />
            <Row label="p-value"            value={p_value.toFixed(6)} />
            <Row label="95% CI"             value={`[${ci_low.toFixed(3)}, ${ci_high.toFixed(3)}]`} />
            <Row
              label="Verdict"
              value={
                <span className={`pill pill-${verdictMeta.pillCls}`}>
                  {verdict.replace(/_/g, ' ')}
                </span>
              }
            />
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────

function MetricCard({ label, value, sub, accent }) {
  return (
    <div className="metric-card" style={{ '--card-accent': accent }}>
      <div className="metric-label">{label}</div>
      <div className="metric-value" style={{ fontSize: '20px', color: accent }}>{value}</div>
      <div className="metric-sub">{sub}</div>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <tr>
      <td style={{ color: 'var(--text-muted)', fontSize: '11px', letterSpacing: '0.1em', textTransform: 'uppercase', width: '44%' }}>
        {label}
      </td>
      <td>{value}</td>
    </tr>
  );
}

function CIBar({ low, high }) {
  // Map [low, high] onto a 0-100% track, where 0 pt is the centre.
  const range  = 40;                                  // display ±20 pts
  const pctLow  = Math.max(0,   ((low  + range / 2) / range) * 100);
  const pctHigh = Math.min(100, ((high + range / 2) / range) * 100);
  const zeroPct = (range / 2 / range) * 100;          // 50%

  return (
    <div className="ci-track">
      <div
        className="ci-fill"
        style={{ left: `${pctLow}%`, width: `${pctHigh - pctLow}%` }}
      />
      <div className="ci-zero" style={{ left: `${zeroPct}%` }} />
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────

function ciCrossesZero(low, high) { return low <= 0 && high >= 0; }

function issAccent(iss) {
  if (iss < 0.05)  return 'var(--green)';
  if (iss < 0.15)  return 'var(--amber)';
  return 'var(--red)';
}

function getVerdictMeta(verdict) {
  const map = {
    no_significant_difference:          { label: '✓ No significant difference detected',          cls: 'none',     pillCls: 'green' },
    marginal_sensitivity:               { label: '~ Marginal sensitivity — inconclusive',          cls: 'marginal', pillCls: 'amber' },
    low_sensitivity_detected:           { label: '⚠ Low identity sensitivity detected',           cls: 'marginal', pillCls: 'amber' },
    identity_sensitivity_detected:      { label: '✕ Identity sensitivity detected',               cls: 'detected', pillCls: 'red'   },
    strong_identity_sensitivity_detected:{ label: '✕ Strong identity sensitivity detected',       cls: 'strong',   pillCls: 'red'   },
  };
  return map[verdict] || { label: verdict, cls: 'marginal', pillCls: 'amber' };
}