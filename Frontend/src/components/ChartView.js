import React, { useRef, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

/**
 * ChartView — renders a side-by-side bar chart comparing
 * Group A (privileged signal) vs Group B (marginalised signal) scores.
 *
 * Props:
 *   result  — AuditResult object from the backend
 */
export default function ChartView({ result }) {
  if (!result) return null;

  const {
    mean_score_group_a,
    mean_score_group_b,
    identity_variable,
    iss_score,
  } = result;

  // Build score bucket distribution (simulated from means for visualisation)
  // In a production build you'd return per-sample scores from the backend.
  const groupALabel = getGroupALabel(identity_variable);
  const groupBLabel = getGroupBLabel(identity_variable);

  const data = {
    labels: [groupALabel, groupBLabel],
    datasets: [
      {
        label: 'Avg hiring score (0–100)',
        data: [
          parseFloat(mean_score_group_a.toFixed(1)),
          parseFloat(mean_score_group_b.toFixed(1)),
        ],
        backgroundColor: ['rgba(0,229,180,0.25)', 'rgba(255,77,109,0.25)'],
        borderColor:     ['rgba(0,229,180,0.9)',   'rgba(255,77,109,0.9)'],
        borderWidth: 1.5,
        borderRadius: 6,
        barThickness: 56,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#18181f',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        titleColor: '#f0f0f5',
        bodyColor: '#8b8b9e',
        padding: 12,
        callbacks: {
          label: ctx => ` Score: ${ctx.parsed.y.toFixed(1)} / 100`,
        },
      },
    },
    scales: {
      x: {
        grid:  { color: 'rgba(255,255,255,0.04)' },
        ticks: { color: '#8b8b9e', font: { family: "'DM Mono', monospace", size: 12 } },
        border: { color: 'rgba(255,255,255,0.07)' },
      },
      y: {
        min: 0, max: 100,
        grid:  { color: 'rgba(255,255,255,0.04)' },
        ticks: {
          color: '#8b8b9e',
          font: { family: "'DM Mono', monospace", size: 11 },
          callback: v => `${v}`,
        },
        border: { color: 'rgba(255,255,255,0.07)' },
      },
    },
  };

  const gap = (mean_score_group_a - mean_score_group_b).toFixed(1);

  return (
    <div>
      {/* Score diff annotation */}
      <div style={{
        display: 'flex',
        gap: '24px',
        marginBottom: '16px',
        flexWrap: 'wrap',
      }}>
        <ScorePill label={groupALabel} value={mean_score_group_a} color="var(--accent)" />
        <ScorePill label={groupBLabel} value={mean_score_group_b} color="var(--red)" />
        <ScorePill label="Gap" value={`+${gap} pts`} color="var(--amber)" raw />
        <ScorePill label="ISS" value={iss_score.toFixed(4)} color="var(--text-secondary)" raw />
      </div>

      <div className="chart-wrapper">
        <Bar data={data} options={options} />
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: '20px', marginTop: '12px', flexWrap: 'wrap' }}>
        <LegendItem color="rgba(0,229,180,0.9)"  label={`${groupALabel} — privileged signal`} />
        <LegendItem color="rgba(255,77,109,0.9)" label={`${groupBLabel} — marginalised signal`} />
      </div>
    </div>
  );
}

function ScorePill({ label, value, color, raw }) {
  return (
    <div>
      <div style={{ fontSize: '10px', letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '3px' }}>
        {label}
      </div>
      <div style={{ fontFamily: "'Syne', sans-serif", fontSize: '22px', fontWeight: '700', color }}>
        {raw ? value : `${parseFloat(value).toFixed(1)}`}
      </div>
    </div>
  );
}

function LegendItem({ color, label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
      <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: color, flexShrink: 0 }} />
      {label}
    </div>
  );
}

// ── Label helpers ─────────────────────────────────────────────────

const LABELS = {
  gender:               ['Male-coded names',   'Female-coded names'],
  caste_hindu_muslim:   ['Upper-caste Hindu',  'Muslim names'],
  caste_upper_sc:       ['Upper-caste',        'SC/ST names'],
  caste_upper_obc:      ['Upper-caste',        'OBC names'],
  college_iit_unknown:  ['IIT / IIM',          'Unknown college'],
  college_iit_state:    ['IIT / IIM',          'State university'],
  location_metro_tier3: ['Metro city',         'Tier-3 city'],
  age_young_senior:     ['Age 24-28',          'Age 38-43'],
};

function getGroupALabel(v) { return (LABELS[v] || ['Group A', 'Group B'])[0]; }
function getGroupBLabel(v) { return (LABELS[v] || ['Group A', 'Group B'])[1]; }