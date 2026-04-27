/**
 * api.js — DHARITRI Frontend API Utilities
 * -----------------------------------------
 * All HTTP calls to the backend go through this file.
 * Base URL is picked up from the CRA proxy (package.json → "proxy")
 * or from REACT_APP_API_URL in .env if deployed separately.
 */

const BASE_URL = process.env.REACT_APP_API_URL || '';

// ── Generic request helper ────────────────────────────────────────

async function request(method, path, body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, options);
  const data = await res.json();

  if (!res.ok) {
    const msg = data?.detail || data?.error || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

// ── Public API ────────────────────────────────────────────────────

/**
 * Health check — confirms backend is reachable.
 * @returns {Promise<{status: string}>}
 */
export async function healthCheck() {
  return request('GET', '/health');
}

/**
 * List all supported experiment types from the backend.
 * @returns {Promise<{experiments: Array<{identity_variable, description}>}>}
 */
export async function listExperiments() {
  return request('GET', '/experiments');
}

/**
 * Run a full fairness audit.
 *
 * @param {Object} payload
 * @param {Object} payload.target             - { type, model_name?, endpoint?, api_key? }
 * @param {string} payload.base_input         - Resume template text
 * @param {string} payload.identity_variable  - e.g. "gender", "caste_hindu_muslim"
 * @param {number} payload.sample_size        - 10–200
 *
 * @returns {Promise<AuditResult>}
 *
 * AuditResult shape:
 * {
 *   identity_variable, description,
 *   iss_score, p_value, confidence_interval,
 *   verdict, mean_score_group_a, mean_score_group_b,
 *   n_samples_per_group
 * }
 */
export async function runAudit(payload) {
  return request('POST', '/audit', payload);
}

// ── Default request payloads (used by the API Simulator) ─────────

export const DEFAULT_REQUEST = {
  target: {
    type: 'seeded',
  },
  base_input:
    'Software engineer with 4 years of experience. ' +
    'Skilled in Python, Django, PostgreSQL, and Docker. ' +
    'Delivered 3 production microservices serving 100k+ daily requests.',
  identity_variable: 'gender',
  sample_size: 50,
};

export const EXAMPLE_RESPONSE = {
  identity_variable: 'gender',
  description: 'Male-coded names vs Female-coded names',
  iss_score: 0.082,
  p_value: 0.031,
  confidence_interval: [4.12, 11.87],
  verdict: 'identity_sensitivity_detected',
  mean_score_group_a: 67.4,
  mean_score_group_b: 56.8,
  n_samples_per_group: 50,
};